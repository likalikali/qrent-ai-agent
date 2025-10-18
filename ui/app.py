import streamlit as st
import os
import json
import hashlib
import uuid
from datetime import datetime, timedelta
from pathlib import Path
import importlib.util
import sqlite3

# 设置页面配置
st.set_page_config(
    page_title="Qrent AI Agent",
    layout="wide",
    page_icon="🏠"
)

# 导入SQLite相关模块
import sqlite3

# 数据库文件路径
db_path = Path(__file__).parent / "qrent_agent.db"

# 初始化数据库
def init_database():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 创建邀请码表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS invitations (
        code TEXT PRIMARY KEY,
        created_at TEXT,
        expires_at TEXT,
        max_uses INTEGER,
        used_count INTEGER
    )
    ''')
    
    # 创建报告表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reports (
        report_id TEXT PRIMARY KEY,
        created_at TEXT,
        invitation_code TEXT,
        report_data TEXT,
        FOREIGN KEY (invitation_code) REFERENCES invitations(code)
    )
    ''')
    
    # 创建邀请码与报告的关联表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS invitation_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invitation_code TEXT,
        report_id TEXT,
        created_at TEXT,
        FOREIGN KEY (invitation_code) REFERENCES invitations(code),
        FOREIGN KEY (report_id) REFERENCES reports(report_id)
    )
    ''')
    
    conn.commit()
    conn.close()

# 邀请码管理类 - 使用SQLite数据库
class InvitationManager:
    def __init__(self, db_path):
        self.db_path = db_path
        init_database()  # 确保数据库已初始化
    
    def _execute_query(self, query, params=(), commit=False):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(query, params)
        
        if commit:
            conn.commit()
            result = None
        else:
            result = cursor.fetchall()
        
        conn.close()
        return result
    
    def generate_invitation_code(self, max_uses=1, expires_days=30):
        code = str(uuid.uuid4()).split('-')[0].upper()
        created_at = datetime.now().isoformat()
        expires_at = (datetime.now() + timedelta(days=expires_days)).isoformat()
        
        query = '''
        INSERT INTO invitations (code, created_at, expires_at, max_uses, used_count)
        VALUES (?, ?, ?, ?, ?)
        '''
        self._execute_query(query, (code, created_at, expires_at, max_uses, 0), commit=True)
        
        return code
    
    def validate_invitation(self, code):
        query = '''
        SELECT expires_at, max_uses, used_count FROM invitations WHERE code = ?
        '''
        result = self._execute_query(query, (code,))
        
        if not result:
            return False, "邀请码不存在"
        
        expires_at, max_uses, used_count = result[0]
        
        # 检查是否过期
        if datetime.now().isoformat() > expires_at:
            return False, "邀请码已过期"
        
        # 检查使用次数
        if used_count >= max_uses:
            return False, "邀请码使用次数已达上限"
        
        return True, "邀请码有效"
    
    def use_invitation(self, code):
        query = '''
        UPDATE invitations SET used_count = used_count + 1 WHERE code = ?
        '''
        self._execute_query(query, (code,), commit=True)
        return True
    
    def add_report_to_invitation(self, code, report_id):
        created_at = datetime.now().isoformat()
        query = '''
        INSERT INTO invitation_reports (invitation_code, report_id, created_at)
        VALUES (?, ?, ?)
        '''
        self._execute_query(query, (code, report_id, created_at), commit=True)
        return True
    
    def get_reports_for_invitation(self, code):
        query = '''
        SELECT report_id, created_at FROM invitation_reports WHERE invitation_code = ?
        '''
        results = self._execute_query(query, (code,))
        
        reports = []
        for report_id, created_at in results:
            reports.append({
                'report_id': report_id,
                'created_at': created_at
            })
        
        return reports
    
    def invitation_exists(self, code):
        query = '''
        SELECT 1 FROM invitations WHERE code = ?
        '''
        result = self._execute_query(query, (code,))
        return len(result) > 0
    
    def add_invitation(self, code, max_uses=5, expires_days=30):
        # 用于添加测试邀请码
        if not self.invitation_exists(code):
            created_at = datetime.now().isoformat()
            expires_at = (datetime.now() + timedelta(days=expires_days)).isoformat()
            
            query = '''
            INSERT INTO invitations (code, created_at, expires_at, max_uses, used_count)
            VALUES (?, ?, ?, ?, ?)
            '''
            self._execute_query(query, (code, created_at, expires_at, max_uses, 0), commit=True)

# 报告管理类 - 使用SQLite数据库
class ReportManager:
    def __init__(self, db_path):
        self.db_path = db_path
    
    def _execute_query(self, query, params=(), commit=False):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(query, params)
        
        if commit:
            conn.commit()
            result = None
        else:
            result = cursor.fetchall()
        
        conn.close()
        return result
    
    def save_report(self, report_data, invitation_code):
        report_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()
        
        # 将报告数据转换为JSON字符串
        report_data_json = json.dumps(report_data, ensure_ascii=False)
        
        query = '''
        INSERT INTO reports (report_id, created_at, invitation_code, report_data)
        VALUES (?, ?, ?, ?)
        '''
        self._execute_query(query, (report_id, created_at, invitation_code, report_data_json), commit=True)
        
        return report_id
    
    def get_report(self, report_id):
        query = '''
        SELECT report_id, created_at, invitation_code, report_data FROM reports WHERE report_id = ?
        '''
        result = self._execute_query(query, (report_id,))
        
        if not result:
            return None
        
        report_id, created_at, invitation_code, report_data_json = result[0]
        
        # 将JSON字符串转换回Python对象
        report_data = json.loads(report_data_json)
        
        return {
            'report_id': report_id,
            'created_at': created_at,
            'invitation_code': invitation_code,
            'report_data': report_data
        }
    
    def get_reports_by_invitation(self, invitation_code):
        query = '''
        SELECT report_id, created_at, invitation_code, report_data 
        FROM reports 
        WHERE invitation_code = ? 
        ORDER BY created_at DESC
        '''
        results = self._execute_query(query, (invitation_code,))
        
        reports = []
        for report_id, created_at, invitation_code, report_data_json in results:
            # 将JSON字符串转换回Python对象
            report_data = json.loads(report_data_json)
            
            reports.append({
                'report_id': report_id,
                'created_at': created_at,
                'invitation_code': invitation_code,
                'report_data': report_data
            })
        
        return reports

# 初始化管理器
invitation_manager = InvitationManager(db_path)
report_manager = ReportManager(db_path)

# 生成测试邀请码（使用SQLite数据库）
def generate_test_invitations():
    test_codes = ['TEST01', 'TEST02', 'TEST03']
    for code in test_codes:
        invitation_manager.add_invitation(code, max_uses=5, expires_days=30)

# 生成测试邀请码
generate_test_invitations()

# 页面导航函数
def show_invitation_page():
    st.title("🔑 Qrent AI Agent - 邀请码验证")
    st.markdown("---")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 欢迎使用 Qrent AI 租房助手")
        st.markdown("\n")
        st.markdown("**Qrent AI Agent** 是一款基于人工智能的租房助手，可以帮助您：")
        st.markdown("\n")
        st.markdown("- 📝 通过智能问卷了解您的租房需求")
        st.markdown("- 🔍 进行专业的需求评估和分析")
        st.markdown("- 💬 提供个性化的房源咨询服务")
        st.markdown("- 📊 生成详细的租房报告")
        st.markdown("\n")
        st.markdown("**为了保证服务质量，本系统采用邀请码制度。**")
        st.markdown("请输入您的邀请码以开始使用。")
        
        # 测试邀请码提示
        with st.expander("💡 测试邀请码"):
            st.info("测试邀请码: TEST01, TEST02, TEST03")
    
    with col2:
        st.markdown("### 输入邀请码")
        invitation_code = st.text_input("请输入您的邀请码", placeholder="例如：ABC123")
        
        if st.button("验证并进入", type="primary", use_container_width=True):
            if not invitation_code:
                st.warning("请输入邀请码")
            else:
                is_valid, message = invitation_manager.validate_invitation(invitation_code.upper())
                if is_valid:
                    # 使用邀请码
                    invitation_manager.use_invitation(invitation_code.upper())
                    # 保存到会话状态
                    st.session_state.invitation_code = invitation_code.upper()
                    st.session_state.page = "main_app"
                    st.success(f"验证成功！{message}")
                    st.rerun()
                else:
                    st.error(f"验证失败: {message}")
        
        st.markdown("\n")
        st.markdown("### 找回历史报告")
        recover_code = st.text_input("输入邀请码查看历史报告", placeholder="输入您之前使用的邀请码")
        
        if st.button("查看历史报告", use_container_width=True):
            if not recover_code:
                st.warning("请输入邀请码")
            else:
                reports = report_manager.get_reports_by_invitation(recover_code.upper())
                if reports:
                    st.session_state.recover_invitation_code = recover_code.upper()
                    st.session_state.recover_reports = reports
                    st.session_state.page = "report_recovery"
                    st.success("找到历史报告！")
                    st.rerun()
                else:
                    st.info("未找到该邀请码的历史报告")

# 报告恢复页面
def show_report_recovery_page():
    st.title("📋 历史报告恢复")
    st.markdown("---")
    
    st.markdown(f"### 邀请码: {st.session_state.recover_invitation_code}")
    st.markdown(f"找到 **{len(st.session_state.recover_reports)}** 份历史报告")
    st.markdown("---")
    
    for i, report in enumerate(st.session_state.recover_reports):
        with st.expander(f"报告 {i+1} - {report['created_at'][:10]}"):
            st.markdown(f"**报告ID:** {report['report_id']}")
            st.markdown(f"**创建时间:** {report['created_at']}")
            
            # 显示报告内容摘要
            report_data = report.get('report_data', {})
            if 'report_type' in report_data:
                st.markdown(f"**报告类型:** {report_data['report_type']}")
            if 'summary' in report_data:
                st.markdown("**报告摘要:**")
                st.markdown(report_data['summary'][:200] + "..." if len(report_data['summary']) > 200 else report_data['summary'])
            
            # 下载按钮
            report_json = json.dumps(report, ensure_ascii=False, indent=2)
            st.download_button(
                label="下载报告",
                data=report_json,
                file_name=f"qrent_report_{report['created_at'][:10]}_{report['report_id'][:8]}.json",
                mime="application/json",
                key=f"download_{report['report_id']}"
            )
    
    if st.button("返回邀请码页面", type="secondary"):
        st.session_state.pop("recover_invitation_code", None)
        st.session_state.pop("recover_reports", None)
        st.session_state.page = "invitation"
        st.rerun()

# 主应用页面 - 加载并运行原有的AIstreamlit应用
def show_main_app():
    # 导入原有的AIstreamlit模块
    st.sidebar.markdown(f"**当前邀请码:** {st.session_state.invitation_code}")
    
    # 修改report.py中的show_report_interface函数，添加保存报告功能
    original_report_module_path = Path(__file__).parent / "report.py"
    if original_report_module_path.exists():
        # 动态导入并修改report模块
        spec = importlib.util.spec_from_file_location("modified_report", original_report_module_path)
        modified_report = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modified_report)
        
        # 保存原始函数
        original_show_report_interface = modified_report.show_report_interface
        
        # 定义包装函数以添加保存功能
        def wrapped_show_report_interface(*args, **kwargs):
            # 显示原始报告界面
            original_show_report_interface(*args, **kwargs)
            
            # 添加保存报告按钮
            if st.session_state.get('report_agent') and st.session_state.get('questionnaire_data'):
                if st.button("💾 保存报告到邀请码", type="primary"):
                    # 收集报告数据
                    report_data = {
                        'report_type': "综合报告",
                        'questionnaire_data': st.session_state.questionnaire_data,
                        'history': st.session_state.get('history', []),
                        'summary': "这是一份由Qrent AI Agent生成的租房报告"
                    }
                    
                    # 保存报告
                    report_id = report_manager.save_report(report_data, st.session_state.invitation_code)
                    # 关联到邀请码
                    invitation_manager.add_report_to_invitation(st.session_state.invitation_code, report_id)
                    st.success(f"报告保存成功！报告ID: {report_id[:8]}")
        
        # 替换模块中的函数
        modified_report.show_report_interface = wrapped_show_report_interface
    
    # 导入并运行AIstreamlit.py
    aistreamlit_path = Path(__file__).parent / "AIstreamlit.py"
    if aistreamlit_path.exists():
        try:
            # 动态导入并运行AIstreamlit
            spec = importlib.util.spec_from_file_location("AIstreamlit", aistreamlit_path)
            aistreamlit = importlib.util.module_from_spec(spec)
            
            # 将修改后的report模块注入到AIstreamlit的命名空间
            aistreamlit.__dict__['report'] = modified_report
            
            spec.loader.exec_module(aistreamlit)
            
            # 调用主函数
            if hasattr(aistreamlit, 'main'):
                aistreamlit.main()
        except Exception as e:
            st.error(f"加载应用时出错: {e}")
            st.exception(e)
    else:
        st.error("找不到AIstreamlit.py文件")
    
    # 添加返回按钮到侧边栏
    if st.sidebar.button("🔄 返回邀请码页面"):
        # 清除会话状态
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.session_state.page = "invitation"
        st.rerun()

# 主页面导航
if 'page' not in st.session_state:
    st.session_state.page = "invitation"

if st.session_state.page == "invitation":
    show_invitation_page()
elif st.session_state.page == "main_app":
    show_main_app()
elif st.session_state.page == "report_recovery":
    show_report_recovery_page()

# 页脚
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #666; font-size: 0.8em;">
        Qrent AI Agent | 专业租房智能助手
    </div>
    """, 
    unsafe_allow_html=True
)