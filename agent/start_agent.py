#!/usr/bin/env python3
"""
Privik Endpoint Agent Startup Script
Main entry point for the Privik endpoint agent
"""

import asyncio
import sys
import os
import signal
import argparse
from pathlib import Path

# Add the agent directory to the Python path
agent_dir = Path(__file__).parent
sys.path.insert(0, str(agent_dir))

from agent import PrivikAgent
import structlog

def setup_logging(log_level: str = "INFO", log_file: str = None):
    """Setup structured logging."""
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    
    if log_file:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

def signal_handler(signum, frame):
    """Handle shutdown signals."""
    print(f"\nReceived signal {signum}. Shutting down gracefully...")
    sys.exit(0)

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Privik Endpoint Agent")
    parser.add_argument(
        "--config", 
        help="Path to configuration file"
    )
    parser.add_argument(
        "--log-level", 
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )
    parser.add_argument(
        "--log-file",
        help="Log file path (optional)"
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run as daemon"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="Privik Endpoint Agent 1.0.0"
    )
    
    args = parser.parse_args()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Setup logging
    setup_logging(args.log_level, args.log_file)
    logger = structlog.get_logger()
    
    # Print banner
    print("=" * 60)
    print("🛡️  Privik Endpoint Agent v1.0.0")
    print("   AI-powered, zero-trust email security")
    print("=" * 60)
    
    try:
        # Create and run agent
        agent = PrivikAgent(config_path=args.config)
        
        # Run the agent
        success = asyncio.run(agent.run())
        
        if success:
            logger.info("Agent completed successfully")
            return 0
        else:
            logger.error("Agent failed")
            return 1
            
    except KeyboardInterrupt:
        logger.info("Agent stopped by user")
        return 0
    except Exception as e:
        logger.error("Fatal error", error=str(e))
        return 1

if __name__ == "__main__":
    sys.exit(main())
