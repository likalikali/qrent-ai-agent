import streamlit as st
import os
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path

# 设置页面配置
st.set_page_config(
    page_title="Qrent AI Agent - 邀请码管理",
    layout="wide",
    page_icon="🔑"
)

# 确保数据目录存在
data_dir = Path(__file__).parent / "data"
data_dir.mkdir(exist_ok=True)

# 邀请码管理类
class InvitationManager:
    def __init__(self, data_dir):
        self.invitations_file = data_dir / "invitations.json"
        self.load_invitations()
    
    def load_invitations(self):
        if self.invitations_file.exists():
            try:
                with open(self.invitations_file, 'r', encoding='utf-8') as f:
                    self.invitations = json.load(f)
            except:
                self.invitations = {}
        else:
            self.invitations = {}
    
    def save_invitations(self):
        with open(self.invitations_file, 'w', encoding='utf-8') as f:
            json.dump(self.invitations, f, ensure_ascii=False, indent=2)
    
    def generate_invitation_code(self, max_uses=1, expires_days=30):
        code = str(uuid.uuid4()).split('-')[0].upper()
        expiry = (datetime.now() + timedelta(days=expires_days)).isoformat()
        
        self.invitations[code] = {
            'created_at': datetime.now().isoformat(),
            'expires_at': expiry,
            'max_uses': max_uses,
            'used_count': 0,
            'reports': []
        }
        
        self.save_invitations()
        return code
    
    def delete_invitation(self, code):
        if code in self.invitations:
            del self.invitations[code]
            self.save_invitations()
            return True
        return False
    
    def get_all_invitations(self):
        return self.invitations
    
    def get_invitation_stats(self):
        total = len(self.invitations)
        active = 0
        used = 0
        expired = 0
        
        now = datetime.now().isoformat()
        
        for code, data in self.invitations.items():
            if now > data['expires_at']:
                expired += 1
            elif data['used_count'] >= data['max_uses']:
                used += 1
            else:
                active += 1
        
        return {
            'total': total,
            'active': active,
            'used': used,
            'expired': expired
        }

# 初始化管理器
invitation_manager = InvitationManager(data_dir)

# 页面标题
st.title("🔑 Qrent AI Agent - 邀请码管理系统")
st.markdown("---")

# 统计信息
stats = invitation_manager.get_invitation_stats()
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("总邀请码数", stats['total'])
with col2:
    st.metric("有效邀请码", stats['active'])
with col3:
    st.metric("已用完邀请码", stats['used'])
with col4:
    st.metric("已过期邀请码", stats['expired'])

st.markdown("---")

# 生成邀请码部分
st.subheader("🎯 生成新邀请码")

col1, col2, col3 = st.columns(3)

with col1:
    max_uses = st.number_input("最大使用次数", min_value=1, max_value=100, value=1)
with col2:
    expires_days = st.number_input("有效期（天）", min_value=1, max_value=365, value=30)
with col3:
    quantity = st.number_input("生成数量", min_value=1, max_value=10, value=1)

if st.button("生成邀请码", type="primary"):
    codes = []
    for _ in range(quantity):
        code = invitation_manager.generate_invitation_code(max_uses, expires_days)
        codes.append(code)
    
    st.success(f"成功生成 {quantity} 个邀请码！")
    
    # 显示生成的邀请码
    for code in codes:
        st.code(code)
    
    # 提供下载选项
    if quantity > 1:
        codes_text = "\n".join(codes)
        st.download_button(
            label="下载邀请码列表",
            data=codes_text,
            file_name=f"invitation_codes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )

st.markdown("---")

# 邀请码管理部分
st.subheader("📋 邀请码管理")

# 搜索功能
search_code = st.text_input("搜索邀请码")

# 过滤选项
st.markdown("### 过滤选项")
filter_col1, filter_col2 = st.columns(2)

with filter_col1:
    status_filter = st.selectbox(
        "状态过滤",
        ["全部", "有效", "已用完", "已过期"]
    )

# 获取并过滤邀请码
invitations = invitation_manager.get_all_invitations()
filtered_invitations = {}

now = datetime.now().isoformat()

for code, data in invitations.items():
    # 搜索过滤
    if search_code and search_code.upper() not in code:
        continue
    
    # 状态过滤
    if status_filter == "有效":
        if now > data['expires_at'] or data['used_count'] >= data['max_uses']:
            continue
    elif status_filter == "已用完":
        if data['used_count'] < data['max_uses']:
            continue
    elif status_filter == "已过期":
        if now <= data['expires_at']:
            continue
    
    filtered_invitations[code] = data

# 显示邀请码列表
st.markdown(f"### 邀请码列表（共 {len(filtered_invitations)} 个）")

if filtered_invitations:
    # 使用表格显示
    data_to_display = []
    for code, data in filtered_invitations.items():
        # 判断状态
        if now > data['expires_at']:
            status = "已过期"
        elif data['used_count'] >= data['max_uses']:
            status = "已用完"
        else:
            status = "有效"
        
        # 格式化日期
        created_at = datetime.fromisoformat(data['created_at']).strftime('%Y-%m-%d %H:%M')
        expires_at = datetime.fromisoformat(data['expires_at']).strftime('%Y-%m-%d %H:%M')
        
        data_to_display.append({
            '邀请码': code,
            '创建时间': created_at,
            '过期时间': expires_at,
            '最大使用次数': data['max_uses'],
            '已使用次数': data['used_count'],
            '状态': status,
            '报告数量': len(data.get('reports', []))
        })
    
    # 显示表格
    st.dataframe(data_to_display)
    
    # 删除选中的邀请码
    st.markdown("### 删除邀请码")
    code_to_delete = st.selectbox("选择要删除的邀请码", list(filtered_invitations.keys()))
    
    if st.button("删除邀请码", type="destructive"):
        if invitation_manager.delete_invitation(code_to_delete):
            st.success(f"邀请码 {code_to_delete} 已删除")
            st.rerun()
        else:
            st.error("删除失败")
else:
    st.info("没有找到符合条件的邀请码")

st.markdown("---")

# 导出所有邀请码
if st.button("导出所有邀请码"):
    export_data = []
    for code, data in invitations.items():
        # 判断状态
        if now > data['expires_at']:
            status = "已过期"
        elif data['used_count'] >= data['max_uses']:
            status = "已用完"
        else:
            status = "有效"
        
        export_data.append({
            '邀请码': code,
            '创建时间': data['created_at'],
            '过期时间': data['expires_at'],
            '最大使用次数': data['max_uses'],
            '已使用次数': data['used_count'],
            '状态': status,
            '报告数量': len(data.get('reports', []))
        })
    
    # 转换为JSON格式
    export_json = json.dumps(export_data, ensure_ascii=False, indent=2)
    
    st.download_button(
        label="下载邀请码数据",
        data=export_json,
        file_name=f"all_invitations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json"
    )

# 页脚
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #666; font-size: 0.8em;">
        Qrent AI Agent | 邀请码管理系统
    </div>
    """, 
    unsafe_allow_html=True
)