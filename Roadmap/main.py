#!/usr/bin/env python3
"""
LeetCode Company-wise Interview Questions Analyzer

This script provides a command-line interface to analyze LeetCode questions
for different companies and time ranges.

The repository is cloned on-demand and cleaned up after each query.

Usage:
    python main.py --company amazon --time-range 3_months
    python main.py --company google --time-range 30_days --export
    python main.py --list-companies
"""

import argparse
import json
from leetcode_analyzer import LeetCodeAnalyzer

def main():
    parser = argparse.ArgumentParser(description='Analyze LeetCode company-wise interview questions')
    
    # List companies option
    parser.add_argument('--list-companies', action='store_true', 
                       help='List all available companies')
    
    # Required arguments
    parser.add_argument('--company', type=str, 
                       help='Company name (e.g., amazon, google, microsoft)')
    parser.add_argument('--time-range', type=str, 
                       choices=['30_days', '3_months', '6_months', 'more_than_6_months', 'all_time'],
                       help='Time range for analysis')
    
    # Optional arguments
    parser.add_argument('--format', type=str, default='json',
                       choices=['json', 'chatbot'],
                       help='Output format (default: json)')
    parser.add_argument('--export', action='store_true',
                       help='Export results to CSV file')
    parser.add_argument('--output', type=str,
                       help='Output file path for CSV export')
    parser.add_argument('--no-cleanup', action='store_true',
                       help='Keep temporary files (for debugging)')
    
    args = parser.parse_args()
    
    # Use context manager for automatic cleanup
    cleanup_after = not args.no_cleanup
    
    try:
        with LeetCodeAnalyzer(cleanup_after=cleanup_after) as analyzer:
            
            # List companies
            if args.list_companies:
                companies = analyzer.get_available_companies()
                print(f"Available Companies ({len(companies)}):")
                for i, company in enumerate(companies, 1):
                    print(f"{i:3d}. {company}")
                return
            
            # Validate required arguments
            if not args.company or not args.time_range:
                print("Error: --company and --time-range are required")
                print("Use --list-companies to see available companies")
                print("Use --help to see all options")
                return
            
            # Perform analysis
            print(f"Analyzing {args.company} for {args.time_range.replace('_', ' ').title()}...")
            result = analyzer.analyze_company(args.company, args.time_range)
            
            # Output results
            if args.format == 'chatbot':
                response = analyzer.format_for_chatbot(result)
                print(response, flush=True)
            else:
                print(json.dumps(result, indent=2), flush=True)
            
            # Export to CSV if requested
            if args.export:
                output_path = analyzer.export_to_csv(args.company, args.time_range, args.output)
                print(f"Exported to: {output_path}")
                
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Make sure the company name is correct and data exists")
    except ValueError as e:
        print(f"Error: {e}")
    except RuntimeError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == '__main__':
    main()
