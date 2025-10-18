import json
import os
from pathlib import Path

def export_invitations_and_reports():
    data_dir = Path(__file__).parent / "data"
    
    # 导出邀请码数据
    invitations_file = data_dir / "invitations.json"
    if invitations_file.exists():
        with open(invitations_file, 'r', encoding='utf-8') as f:
            invitations = json.load(f)
        
        with open('exported_invitations.json', 'w', encoding='utf-8') as f:
            json.dump(invitations, f, ensure_ascii=False, indent=2)
        print(f"导出了 {len(invitations)} 个邀请码")
    
    # 导出报告数据
    reports_dir = data_dir / "reports"
    reports = []
    if reports_dir.exists():
        for report_file in reports_dir.glob("*.json"):
            try:
                with open(report_file, 'r', encoding='utf-8') as f:
                    report = json.load(f)
                    reports.append(report)
            except:
                continue
        
        with open('exported_reports.json', 'w', encoding='utf-8') as f:
            json.dump(reports, f, ensure_ascii=False, indent=2)
        print(f"导出了 {len(reports)} 份报告")

export_invitations_and_reports()