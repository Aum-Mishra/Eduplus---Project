import pandas as pd
from pathlib import Path
import json
import tempfile
import shutil
import subprocess
import os
from typing import Dict, List, Optional, Tuple

TIME_RANGE_MAP = {
    "30_days": "thirty-days.csv",
    "3_months": "three-months.csv", 
    "6_months": "six-months.csv",
    "more_than_6_months": "more-than-six-months.csv",
    "all_time": "all.csv"
}

class LeetCodeAnalyzer:
    def __init__(self, cleanup_after=True):
        self.cleanup_after = cleanup_after
        self.temp_dir = None
        self.repo_path = None
        
    def __enter__(self):
        """Context manager entry - clone repository"""
        self._clone_repository()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup"""
        if self.cleanup_after and self.temp_dir:
            self._cleanup()
            
    def _clone_repository(self):
        """Clone the repository to temporary directory"""
        print("📥 Cloning LeetCode repository...")
        
        # Create temporary directory
        self.temp_dir = tempfile.mkdtemp(prefix="leetcode_")
        self.repo_path = Path(self.temp_dir) / "leetcode-companywise-interview-questions"
        
        try:
            # Clone the repository
            result = subprocess.run([
                "git", "clone", 
                "https://github.com/snehasishroy/leetcode-companywise-interview-questions.git",
                str(self.repo_path)
            ], capture_output=True, text=True, cwd=self.temp_dir)
            
            if result.returncode != 0:
                raise RuntimeError(f"Failed to clone repository: {result.stderr}")
                
            print(f"✅ Repository cloned to: {self.repo_path}")
            
        except Exception as e:
            # Cleanup on failure
            if self.temp_dir:
                shutil.rmtree(self.temp_dir, ignore_errors=True)
            raise e
            
    def _cleanup(self):
        """Clean up temporary directory"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            print("🧹 Cleaning up temporary files...")
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            print("✅ Cleanup complete")
            
    def load_company_csv(self, company: str, time_range: str) -> pd.DataFrame:
        """Load CSV for a specific company and time range."""
        if not self.repo_path:
            raise RuntimeError("Repository not cloned. Use context manager.")
            
        if time_range not in TIME_RANGE_MAP:
            raise ValueError(f"Invalid time range. Must be one of: {list(TIME_RANGE_MAP.keys())}")
            
        filename = TIME_RANGE_MAP[time_range]
        file_path = self.repo_path / company.lower() / filename
        
        if not file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")
            
        return pd.read_csv(file_path)
    
    def get_difficulty_summary(self, df: pd.DataFrame) -> Dict[str, int]:
        """Get count of questions by difficulty."""
        return df["Difficulty"].value_counts().to_dict()
    
    def get_total_questions(self, df: pd.DataFrame) -> int:
        """Get total number of questions."""
        return len(df)
    
    def get_question_list(self, df: pd.DataFrame) -> List[Dict]:
        """Get list of all questions with details."""
        return df.to_dict('records')
    
    def analyze_company(self, company: str, time_range: str) -> Dict:
        """Complete analysis for a company and time range."""
        df = self.load_company_csv(company, time_range)
        
        return {
            "company": company,
            "time_range": self._format_time_range(time_range),
            "total_questions": self.get_total_questions(df),
            "difficulty_breakdown": self.get_difficulty_summary(df),
            "questions": self.get_question_list(df),
            "source": "LeetCode company-wise interview dataset"
        }
    
    def _format_time_range(self, time_range: str) -> str:
        """Format time range for display."""
        formats = {
            "30_days": "Last 30 Days",
            "3_months": "Last 3 Months", 
            "6_months": "Last 6 Months",
            "more_than_6_months": "More Than 6 Months",
            "all_time": "All Time"
        }
        return formats.get(time_range, time_range)
    
    def export_to_csv(self, company: str, time_range: str, output_path: Optional[str] = None) -> str:
        """Export questions to CSV file."""
        df = self.load_company_csv(company, time_range)
        
        if output_path is None:
            output_path = f"{company}_{time_range}_questions.csv"
            
        df.to_csv(output_path, index=False)
        return output_path
    
    def get_available_companies(self) -> List[str]:
        """Get list of all available companies."""
        if not self.repo_path:
            raise RuntimeError("Repository not cloned. Use context manager.")
            
        companies = []
        for item in self.repo_path.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                companies.append(item.name)
        return sorted(companies)
    
    def format_for_chatbot(self, analysis_result: Dict) -> str:
        """Format analysis result for chatbot response."""
        result = analysis_result
        
        # Determine number of questions to show based on time range
        questions_to_show = self._get_question_count_for_time_range(result['time_range'])
        
        response = f"""{result['company']} - {result['time_range']}

Total Questions: {result['total_questions']}

Difficulty Breakdown:
"""
        for difficulty, count in result['difficulty_breakdown'].items():
            response += f"- {difficulty}: {count}\n"
            
        response += f"\nQuestions:\n"
        for i, question in enumerate(result['questions'][:questions_to_show], 1):
            response += f"{i}. {question['Title']} ({question['Difficulty']})\n"
            
        if len(result['questions']) > questions_to_show:
            response += f"... and {len(result['questions']) - questions_to_show} more questions\n"
            
        return response
    
    def _get_question_count_for_time_range(self, time_range: str) -> int:
        """Get number of questions to display based on time range."""
        question_counts = {
            "Last 30 Days": 18,      # 15-20 questions
            "Last 3 Months": 36,    # Double of 30 days
            "Last 6 Months": 72,    # Double of 3 months
            "More Than 6 Months": 144,  # Double of 6 months
            "All Time": 288         # Double of more than 6 months
        }
        return question_counts.get(time_range, 18)
