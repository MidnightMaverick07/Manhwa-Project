import argparse
import yaml
import os
from pathlib import Path

# Placeholder for importing pipeline modules once they are created
# from core.pipeline import run_pipeline

def load_config(config_path: str) -> dict:
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def check_directories(config: dict):
    paths = config.get('paths', {})
    for key, path in paths.items():
        Path(path).mkdir(parents=True, exist_ok=True)
        print(f"Ensured directory exists: {path}")

def main():
    parser = argparse.ArgumentParser(description="Manhwa-to-YouTube-Recap Pipeline (Phase 1 MVP)")
    parser.add_argument('--input', type=str, required=True, help="Path to input directory containing manhwa images")
    parser.add_argument('--config', type=str, default="config.yaml", help="Path to config file")
    
    args = parser.parse_args()
    
    config = load_config(args.config)
    
    # Override input dir if provided
    config['paths']['input_dir'] = args.input
    
    check_directories(config)
    
    print("Starting Thin MVP Pipeline...")
    
    from core.pipeline import run_pipeline
    run_pipeline(config)

if __name__ == "__main__":
    main()
