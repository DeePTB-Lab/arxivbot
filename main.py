import argparse
from src.core.app import ArxivBot

def main():
    parser = argparse.ArgumentParser(description="ArXivBot")
    parser.add_argument("--config", default=None, help="Path to config file")
    parser.add_argument("--papers-file", default=None, help="Path to papers history file")
    parser.add_argument("--hunt-file", default=None, help="Path to paper hunt prompt file")
    parser.add_argument("--paper-config", default=None, help="Path to public paper config file")
    
    # Feature Flags
    parser.add_argument("--use-llm", action="store_true", help="Enable LLM filtering and translation")
    parser.add_argument("--deep-scan", action="store_true", help="Enable Deep Scan")
    
    args = parser.parse_args()

    bot = ArxivBot(
        config_path=args.config,
        papers_file=args.papers_file,
        hunt_file=args.hunt_file,
        paper_config_path=args.paper_config,
        use_llm=args.use_llm,
        enable_deep_scan=args.deep_scan
    )
    bot.run()

if __name__ == "__main__":
    main()
