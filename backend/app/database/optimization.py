"""
Database Optimization Module
Handles database performance optimization, indexing, and query optimization
"""

from sqlalchemy import Index, text, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import structlog
from ..core.config import settings

logger = structlog.get_logger()

class DatabaseOptimizer:
    """Handles database optimization and performance tuning"""
    
    def __init__(self):
        self.engine = None
        self.session_factory = None
        
    def create_optimized_engine(self):
        """Create optimized database engine with connection pooling"""
        try:
            # Enhanced connection pool configuration
            pool_config = {
                'poolclass': QueuePool,
                'pool_size': 20,  # Base number of connections
                'max_overflow': 30,  # Additional connections beyond pool_size
                'pool_pre_ping': True,  # Validate connections before use
                'pool_recycle': 3600,  # Recycle connections every hour
                'pool_timeout': 30,  # Timeout for getting connection
                'echo': False,  # Set to True for SQL debugging
            }
            
            # Create optimized engine
            self.engine = create_engine(
                settings.DATABASE_URL,
                **pool_config
            )
            
            # Create session factory
            self.session_factory = sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False
            )
            
            logger.info("Optimized database engine created", 
                       pool_size=pool_config['pool_size'],
                       max_overflow=pool_config['max_overflow'])
            
            return self.engine
            
        except Exception as e:
            logger.error("Error creating optimized database engine", error=str(e))
            raise
    
    def create_performance_indexes(self):
        """Create performance indexes for frequently queried columns"""
        try:
            indexes = [
                # Email table indexes
                Index('idx_emails_received_at', 'emails', 'received_at'),
                Index('idx_emails_sender', 'emails', 'sender'),
                Index('idx_emails_threat_score', 'emails', 'threat_score'),
                Index('idx_emails_ai_verdict', 'emails', 'ai_verdict'),
                Index('idx_emails_status', 'emails', 'status'),
                Index('idx_emails_sender_threat', 'emails', 'sender', 'threat_score'),
                
                # Sandbox analysis indexes
                Index('idx_sandbox_analysis_created_at', 'sandbox_analysis', 'created_at'),
                Index('idx_sandbox_analysis_verdict', 'sandbox_analysis', 'verdict'),
                Index('idx_sandbox_analysis_email_id', 'sandbox_analysis', 'email_id'),
                Index('idx_sandbox_analysis_threat_score', 'sandbox_analysis', 'threat_score'),
                Index('idx_sandbox_analysis_status', 'sandbox_analysis', 'status'),
                
                # Quarantine indexes
                Index('idx_email_quarantine_status', 'email_quarantine', 'status'),
                Index('idx_email_quarantine_created_at', 'email_quarantine', 'created_at'),
                Index('idx_email_quarantine_reason', 'email_quarantine', 'quarantine_reason'),
                Index('idx_email_quarantine_threat_score', 'email_quarantine', 'threat_score'),
                Index('idx_email_quarantine_email_id', 'email_quarantine', 'email_id'),
                
                # Incident correlation indexes
                Index('idx_security_incidents_created_at', 'security_incidents', 'created_at'),
                Index('idx_security_incidents_status', 'security_incidents', 'status'),
                Index('idx_security_incidents_severity', 'security_incidents', 'severity'),
                Index('idx_security_incidents_type', 'security_incidents', 'incident_type'),
                Index('idx_security_incidents_incident_id', 'security_incidents', 'incident_id'),
                
                # Timeline events indexes
                Index('idx_timeline_events_incident_id', 'incident_timeline_events', 'incident_id'),
                Index('idx_timeline_events_event_time', 'incident_timeline_events', 'event_time'),
                Index('idx_timeline_events_type', 'incident_timeline_events', 'event_type'),
                
                # Domain lists indexes
                Index('idx_domain_lists_domain', 'domain_lists', 'domain'),
                Index('idx_domain_lists_type', 'domain_lists', 'list_type'),
                Index('idx_domain_lists_active', 'domain_lists', 'is_active'),
                Index('idx_domain_lists_domain_type', 'domain_lists', 'domain', 'list_type'),
                
                # Threat feed indexes
                Index('idx_threat_feeds_active', 'threat_feeds', 'is_active'),
                Index('idx_threat_feeds_type', 'threat_feeds', 'feed_type'),
                Index('idx_threat_feed_records_created_at', 'threat_feed_records', 'created_at'),
                Index('idx_threat_feed_records_feed_id', 'threat_feed_records', 'feed_id'),
                
                # Integration state indexes
                Index('idx_integration_state_name', 'integration_state', 'name'),
                Index('idx_integration_state_last_sync', 'integration_state', 'last_sync'),
            ]
            
            # Create indexes
            for index in indexes:
                try:
                    index.create(self.engine, checkfirst=True)
                    logger.info("Created index", index_name=index.name)
                except Exception as e:
                    logger.warning("Index creation failed", index_name=index.name, error=str(e))
            
            logger.info("Performance indexes creation completed")
            
        except Exception as e:
            logger.error("Error creating performance indexes", error=str(e))
            raise
    
    def analyze_query_performance(self):
        """Analyze and optimize slow queries"""
        try:
            # Common slow queries to optimize
            slow_queries = [
                # Email analysis queries
                "SELECT * FROM emails WHERE received_at >= ? AND threat_score > ?",
                "SELECT * FROM emails WHERE sender LIKE ? AND ai_verdict = ?",
                
                # Sandbox analysis queries
                "SELECT * FROM sandbox_analysis WHERE created_at >= ? AND verdict = ?",
                "SELECT * FROM sandbox_analysis WHERE email_id IN (SELECT id FROM emails WHERE threat_score > ?)",
                
                # Quarantine queries
                "SELECT * FROM email_quarantine WHERE status = ? AND created_at >= ?",
                "SELECT * FROM email_quarantine WHERE quarantine_reason = ? AND threat_score > ?",
                
                # Incident correlation queries
                "SELECT * FROM security_incidents WHERE status = ? AND created_at >= ?",
                "SELECT * FROM incident_correlations WHERE correlation_type = ? AND correlation_value = ?",
            ]
            
            # Analyze each query
            for query in slow_queries:
                try:
                    result = self.engine.execute(text(f"EXPLAIN QUERY PLAN {query}"))
                    logger.info("Query analysis", query=query, plan=str(result.fetchall()))
                except Exception as e:
                    logger.warning("Query analysis failed", query=query, error=str(e))
            
            logger.info("Query performance analysis completed")
            
        except Exception as e:
            logger.error("Error analyzing query performance", error=str(e))
    
    def optimize_database_settings(self):
        """Optimize database configuration settings"""
        try:
            # SQLite optimization settings
            optimization_queries = [
                "PRAGMA journal_mode = WAL",  # Write-Ahead Logging
                "PRAGMA synchronous = NORMAL",  # Balanced performance/reliability
                "PRAGMA cache_size = -64000",  # 64MB cache
                "PRAGMA temp_store = MEMORY",  # Store temp tables in memory
                "PRAGMA mmap_size = 268435456",  # 256MB memory-mapped I/O
                "PRAGMA optimize",  # Run query optimizer
            ]
            
            with self.engine.connect() as conn:
                for query in optimization_queries:
                    try:
                        conn.execute(text(query))
                        logger.info("Applied database optimization", query=query)
                    except Exception as e:
                        logger.warning("Database optimization failed", query=query, error=str(e))
            
            logger.info("Database optimization settings applied")
            
        except Exception as e:
            logger.error("Error optimizing database settings", error=str(e))
    
    def get_database_stats(self):
        """Get database performance statistics"""
        try:
            stats_queries = {
                'table_sizes': """
                    SELECT name, 
                           (SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=m.name) as row_count
                    FROM sqlite_master m 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                """,
                'index_usage': """
                    SELECT name, sql 
                    FROM sqlite_master 
                    WHERE type='index' AND name NOT LIKE 'sqlite_%'
                """,
                'database_size': "PRAGMA page_count;",
                'cache_hit_ratio': "PRAGMA cache_size;"
            }
            
            stats = {}
            with self.engine.connect() as conn:
                for stat_name, query in stats_queries.items():
                    try:
                        result = conn.execute(text(query))
                        stats[stat_name] = result.fetchall()
                    except Exception as e:
                        logger.warning("Failed to get database stat", stat=stat_name, error=str(e))
                        stats[stat_name] = None
            
            logger.info("Database statistics collected", stats=stats)
            return stats
            
        except Exception as e:
            logger.error("Error getting database statistics", error=str(e))
            return {}

# Global optimizer instance
db_optimizer = DatabaseOptimizer()
