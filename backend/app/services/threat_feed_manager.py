"""
Threat Feed Manager Service
Manages threat intelligence feeds and real-time updates
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import structlog
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models.threat_feed import ThreatFeed, ThreatFeedRecord, ThreatFeedSubscription
from .domain_reputation import DomainReputationService
from .bulk_domain_manager import BulkDomainManager

logger = structlog.get_logger()

class ThreatFeedManager:
    """Manages threat intelligence feeds and updates"""
    
    def __init__(self):
        self.db = SessionLocal()
        self.session = None
        self.running = False
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def start_feed_monitoring(self):
        """Start monitoring all active threat feeds"""
        self.running = True
        logger.info("Starting threat feed monitoring")
        
        while self.running:
            try:
                await self._process_feeds()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error("Error in feed monitoring loop", error=str(e))
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    async def stop_feed_monitoring(self):
        """Stop monitoring threat feeds"""
        self.running = False
        logger.info("Stopping threat feed monitoring")
    
    async def _process_feeds(self):
        """Process all active feeds that need updates"""
        try:
            # Get feeds that need updates
            now = datetime.utcnow()
            feeds = self.db.query(ThreatFeed).filter(
                ThreatFeed.is_active == True,
                ThreatFeed.status == 'active',
                ThreatFeed.next_update <= now
            ).all()
            
            if not feeds:
                return
            
            logger.info("Processing threat feeds", count=len(feeds))
            
            # Process feeds in parallel
            tasks = [self._process_single_feed(feed) for feed in feeds]
            await asyncio.gather(*tasks, return_exceptions=True)
            
        except Exception as e:
            logger.error("Error processing feeds", error=str(e))
    
    async def _process_single_feed(self, feed: ThreatFeed):
        """Process a single threat feed"""
        try:
            logger.info("Processing threat feed", feed_name=feed.name)
            
            if feed.source_type == 'webhook':
                # Webhook feeds are updated by external calls
                return
            elif feed.source_type == 'api':
                await self._update_from_api(feed)
            elif feed.source_type == 'file':
                await self._update_from_file(feed)
            
            # Update feed status
            feed.last_updated = datetime.utcnow()
            feed.next_update = datetime.utcnow() + timedelta(seconds=feed.update_interval)
            feed.error_count = 0
            feed.last_error = None
            self.db.commit()
            
            logger.info("Feed processed successfully", feed_name=feed.name)
            
        except Exception as e:
            logger.error("Error processing feed", feed_name=feed.name, error=str(e))
            
            # Update error status
            feed.error_count += 1
            feed.last_error = str(e)
            feed.next_update = datetime.utcnow() + timedelta(minutes=30)  # Retry in 30 minutes
            
            if feed.error_count >= 5:
                feed.status = 'error'
            
            self.db.commit()
    
    async def _update_from_api(self, feed: ThreatFeed):
        """Update feed from API endpoint"""
        try:
            headers = {}
            if feed.api_key:
                headers['Authorization'] = f'Bearer {feed.api_key}'
            
            async with self.session.get(feed.feed_url, headers=headers) as response:
                if response.status != 200:
                    raise Exception(f"API returned status {response.status}")
                
                data = await response.json()
                await self._process_feed_data(feed, data)
                
        except Exception as e:
            logger.error("API update failed", feed_name=feed.name, error=str(e))
            raise
    
    async def _update_from_file(self, feed: ThreatFeed):
        """Update feed from file (placeholder for file-based feeds)"""
        # This would be implemented for file-based threat feeds
        # For now, we'll skip this implementation
        logger.info("File-based feeds not yet implemented", feed_name=feed.name)
    
    async def _process_feed_data(self, feed: ThreatFeed, data: Any):
        """Process threat feed data and create records"""
        try:
            # Handle different data formats
            if isinstance(data, list):
                indicators = data
            elif isinstance(data, dict):
                if 'indicators' in data:
                    indicators = data['indicators']
                elif 'data' in data:
                    indicators = data['data']
                else:
                    indicators = [data]
            else:
                logger.warning("Unknown data format", feed_name=feed.name)
                return
            
            # Process each indicator
            new_records = 0
            updated_records = 0
            
            for indicator_data in indicators:
                try:
                    # Extract indicator information
                    indicator = self._extract_indicator(indicator_data)
                    if not indicator:
                        continue
                    
                    # Check if record exists
                    existing = self.db.query(ThreatFeedRecord).filter(
                        ThreatFeedRecord.feed_id == feed.id,
                        ThreatFeedRecord.indicator == indicator['indicator']
                    ).first()
                    
                    if existing:
                        # Update existing record
                        existing.last_seen = datetime.utcnow()
                        existing.confidence = indicator.get('confidence', existing.confidence)
                        existing.severity = indicator.get('severity', existing.severity)
                        existing.tags = indicator.get('tags', existing.tags)
                        existing.raw_data = indicator_data
                        updated_records += 1
                    else:
                        # Create new record
                        record = ThreatFeedRecord(
                            feed_id=feed.id,
                            indicator=indicator['indicator'],
                            indicator_type=indicator['type'],
                            threat_type=indicator.get('threat_type', feed.category),
                            confidence=indicator.get('confidence', 0.7),
                            severity=indicator.get('severity', 'medium'),
                            description=indicator.get('description'),
                            source_reference=indicator.get('source_reference'),
                            tags=indicator.get('tags'),
                            raw_data=indicator_data
                        )
                        self.db.add(record)
                        new_records += 1
                
                except Exception as e:
                    logger.error("Error processing indicator", 
                               feed_name=feed.name, 
                               indicator=str(indicator_data)[:100],
                               error=str(e))
            
            self.db.commit()
            
            # Update feed statistics
            feed.total_records = self.db.query(ThreatFeedRecord).filter(
                ThreatFeedRecord.feed_id == feed.id
            ).count()
            
            logger.info("Feed data processed", 
                       feed_name=feed.name,
                       new_records=new_records,
                       updated_records=updated_records)
            
            # Auto-update domain lists if configured
            await self._auto_update_domain_lists(feed, new_records)
            
        except Exception as e:
            logger.error("Error processing feed data", feed_name=feed.name, error=str(e))
            raise
    
    def _extract_indicator(self, data: Any) -> Optional[Dict[str, Any]]:
        """Extract indicator information from feed data"""
        try:
            if isinstance(data, str):
                # Simple string indicator
                return {
                    'indicator': data,
                    'type': self._determine_indicator_type(data),
                    'confidence': 0.7,
                    'severity': 'medium'
                }
            elif isinstance(data, dict):
                # Structured indicator
                indicator = data.get('indicator') or data.get('value') or data.get('domain')
                if not indicator:
                    return None
                
                return {
                    'indicator': indicator,
                    'type': data.get('type', self._determine_indicator_type(indicator)),
                    'threat_type': data.get('threat_type'),
                    'confidence': data.get('confidence', 0.7),
                    'severity': data.get('severity', 'medium'),
                    'description': data.get('description'),
                    'source_reference': data.get('source_reference'),
                    'tags': data.get('tags', [])
                }
            else:
                return None
                
        except Exception as e:
            logger.error("Error extracting indicator", error=str(e))
            return None
    
    def _determine_indicator_type(self, indicator: str) -> str:
        """Determine indicator type from value"""
        if '.' in indicator and not indicator.replace('.', '').replace('-', '').isdigit():
            return 'domain'
        elif indicator.startswith('http'):
            return 'url'
        elif indicator.replace('.', '').isdigit():
            return 'ip'
        else:
            return 'hash'
    
    async def _auto_update_domain_lists(self, feed: ThreatFeed, new_records: int):
        """Automatically update domain lists from threat feed"""
        try:
            if new_records == 0:
                return
            
            # Get new domain indicators from this feed
            new_domains = self.db.query(ThreatFeedRecord).filter(
                ThreatFeedRecord.feed_id == feed.id,
                ThreatFeedRecord.indicator_type == 'domain',
                ThreatFeedRecord.confidence >= feed.confidence_threshold,
                ThreatFeedRecord.first_seen >= datetime.utcnow() - timedelta(hours=1)
            ).all()
            
            if not new_domains:
                return
            
            # Determine list type based on feed category
            list_type = 'blacklist'
            if feed.category == 'whitelist':
                list_type = 'whitelist'
            
            # Add domains to domain list
            bulk_manager = BulkDomainManager()
            
            domain_updates = []
            for domain_record in new_domains:
                domain_updates.append({
                    'domain': domain_record.indicator,
                    'list_type': list_type,
                    'reason': f"Auto-imported from {feed.name}: {domain_record.description or domain_record.threat_type}",
                    'created_by': f"threat_feed_{feed.id}"
                })
            
            # Use bulk domain manager to add domains
            result = await bulk_manager.bulk_update_domains(domain_updates)
            
            logger.info("Auto-updated domain lists", 
                       feed_name=feed.name,
                       domains_added=result.get('successful_updates', 0))
            
        except Exception as e:
            logger.error("Error auto-updating domain lists", 
                        feed_name=feed.name, 
                        error=str(e))
    
    async def add_webhook_update(self, feed_name: str, webhook_data: Any):
        """Process webhook update for a threat feed"""
        try:
            feed = self.db.query(ThreatFeed).filter(
                ThreatFeed.name == feed_name,
                ThreatFeed.source_type == 'webhook'
            ).first()
            
            if not feed:
                logger.warning("Webhook feed not found", feed_name=feed_name)
                return
            
            await self._process_feed_data(feed, webhook_data)
            
            logger.info("Webhook update processed", feed_name=feed_name)
            
        except Exception as e:
            logger.error("Error processing webhook update", 
                        feed_name=feed_name, 
                        error=str(e))
    
    async def get_feed_status(self) -> Dict[str, Any]:
        """Get overall threat feed status"""
        try:
            feeds = self.db.query(ThreatFeed).all()
            
            status = {
                'total_feeds': len(feeds),
                'active_feeds': len([f for f in feeds if f.is_active]),
                'error_feeds': len([f for f in feeds if f.status == 'error']),
                'total_records': sum(f.total_records for f in feeds),
                'last_updates': []
            }
            
            # Get recent updates
            recent_feeds = self.db.query(ThreatFeed).filter(
                ThreatFeed.last_updated.isnot(None)
            ).order_by(ThreatFeed.last_updated.desc()).limit(5).all()
            
            for feed in recent_feeds:
                status['last_updates'].append({
                    'name': feed.name,
                    'last_updated': feed.last_updated.isoformat(),
                    'records': feed.total_records,
                    'status': feed.status
                })
            
            return status
            
        except Exception as e:
            logger.error("Error getting feed status", error=str(e))
            return {'error': str(e)}
    
    async def create_feed(
        self,
        name: str,
        source_type: str,
        feed_url: Optional[str] = None,
        webhook_url: Optional[str] = None,
        api_key: Optional[str] = None,
        category: Optional[str] = None,
        description: Optional[str] = None
    ) -> ThreatFeed:
        """Create a new threat feed"""
        try:
            feed = ThreatFeed(
                name=name,
                source_type=source_type,
                feed_url=feed_url,
                webhook_url=webhook_url,
                api_key=api_key,
                category=category,
                description=description,
                is_active=True,
                status='active'
            )
            
            self.db.add(feed)
            self.db.commit()
            self.db.refresh(feed)
            
            logger.info("Threat feed created", feed_name=name, feed_id=feed.id)
            
            return feed
            
        except Exception as e:
            logger.error("Error creating threat feed", error=str(e))
            self.db.rollback()
            raise
    
    async def delete_feed(self, feed_id: int):
        """Delete a threat feed and its records"""
        try:
            # Delete feed records first
            self.db.query(ThreatFeedRecord).filter(
                ThreatFeedRecord.feed_id == feed_id
            ).delete()
            
            # Delete feed
            feed = self.db.query(ThreatFeed).filter(ThreatFeed.id == feed_id).first()
            if feed:
                self.db.delete(feed)
                self.db.commit()
                
                logger.info("Threat feed deleted", feed_name=feed.name)
            
        except Exception as e:
            logger.error("Error deleting threat feed", error=str(e))
            self.db.rollback()
            raise
