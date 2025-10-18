# -*- coding: utf-8 -*-
import requests
import json
from typing import Dict, Any, Optional


def search_properties_from_questionnaire(questionnaire_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    基于问卷数据搜索房源信息
    
    Args:
        questionnaire_data: 问卷数据字典，包含用户的租房需求
    
    Returns:
        包含房源搜索结果的字典
    """
    try:
        # 提取并转换问卷数据
        min_price = questionnaire_data.get('budget_min')
        max_price = questionnaire_data.get('budget_max')
        room_type = questionnaire_data.get('room_type')
        commute_time = questionnaire_data.get('commute_time')
        target_school = questionnaire_data.get('target_school', 'University of New South Wales')
        
        # 转换通勤时间文本为数值
        max_commute_time = None
        if commute_time:
            commute_mapping = {
                # Chinese versions
                '15分钟以内': 15,
                '30分钟以内': 30,
                '45分钟以内': 45,
                '1小时以内': 60,
                '1小时以上': 120,
                '没有要求': None,
                # English versions
                '15 minutes': 15,
                'Within 15 minutes': 15,
                '30 minutes': 30,
                'Within 30 minutes': 30,
                '45 minutes': 45,
                'Within 45 minutes': 45,
                '1 hour': 60,
                'Within 1 hour': 60,
                'Over 1 hour': 120,
                'No requirement': None,
                'No requirements': None
            }
            max_commute_time = commute_mapping.get(commute_time)
        
        # 调用底层搜索函数
        return search_properties(
            min_price=min_price,
            max_price=max_price,
            target_school=target_school,
            max_commute_time=max_commute_time,
            room_type=room_type,
            page_size=10
        )
        
    except Exception as e:
        return {
            "success": False,
            "error": f"问卷数据处理错误: {str(e)}"
        }


def search_properties(
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    target_school: Optional[str] = None,
    min_commute_time: Optional[int] = None,
    max_commute_time: Optional[int] = None,
    regions: Optional[str] = None,
    room_type: Optional[str] = None,
    bedrooms: Optional[int] = None,
    bathrooms: Optional[int] = None,
    page: int = 1,
    page_size: int = 10
) -> Dict[str, Any]:
    """
    搜索房源信息
    
    Args:
        min_price: 最低价格 (AUD/周)
        max_price: 最高价格 (AUD/周)
        target_school: 目标学校名称
        min_commute_time: 最短通勤时间 (分钟)
        max_commute_time: 最长通勤时间 (分钟)
        regions: 区域代码
        room_type: 房型类型，例如 'studio', '1bedroom', '2bedroom' 等
        bedrooms: 卧室数量
        bathrooms: 卫生间数量
        page: 页码
        page_size: 每页数量
    
    Returns:
        包含房源搜索结果的字典
    """
    try:
        # API端点
        url = "http://139.180.164.78:3201/properties/search"
        
        # 构建请求数据
        payload: Dict[str, Any] = {
            "page": page,
            "pageSize": page_size
        }
        
        # 只添加非空参数
        if min_price is not None:
            payload["minPrice"] = int(min_price)
        if max_price is not None:
            payload["maxPrice"] = int(max_price)
        # targetSchool 是必需参数，如果没有提供则使用默认值
        if target_school is not None:
            payload["targetSchool"] = str(target_school)
        else:
            payload["targetSchool"] = "University of New South Wales"  # 默认学校
        if min_commute_time is not None:
            payload["minCommuteTime"] = int(min_commute_time)
        if max_commute_time is not None:
            payload["maxCommuteTime"] = int(max_commute_time)
        if regions is not None:
            payload["regions"] = str(regions)
            
        # 处理房型：使用bedroom数量而不是roomType
        if room_type is not None:
            room_type_lower = str(room_type).lower()
            if "studio" in room_type_lower:
                payload["minBedrooms"] = 0
                payload["maxBedrooms"] = 0
            elif "1bedroom" in room_type_lower or "1bed" in room_type_lower:
                payload["minBedrooms"] = 1
                payload["maxBedrooms"] = 1
            elif "2bedroom" in room_type_lower or "2bed" in room_type_lower:
                payload["minBedrooms"] = 2
                payload["maxBedrooms"] = 2
            elif "3bedroom" in room_type_lower or "3bed" in room_type_lower:
                payload["minBedrooms"] = 3
                payload["maxBedrooms"] = 3
        
        # 直接指定卧室和卫生间数量（优先级高于room_type）
        if bedrooms is not None:
            payload["minBedrooms"] = int(bedrooms)
            payload["maxBedrooms"] = int(bedrooms)
        if bathrooms is not None:
            payload["minBathrooms"] = int(bathrooms)
            payload["maxBathrooms"] = int(bathrooms)
        
        # 设置请求头
        headers = {
            "Content-Type": "application/json"
        }
        
        # 发送POST请求
        response = requests.post(
            url,
            headers=headers,
            data=json.dumps(payload),
            timeout=30
        )
        
        # 检查响应状态
        if response.status_code == 200:
            result = response.json()
            
            # 格式化返回结果
            return {
                "success": True,
                "count": len(result.get("properties", [])),
                "properties": result.get("properties", []),
                "total": result.get("totalCount", 0),
                "filtered_count": result.get("filteredCount", 0),
                "average_price": result.get("averagePrice", 0),
                "average_commute_time": result.get("averageCommuteTime", 0),
                "top_regions": result.get("topRegions", []),
                "page": page,
                "page_size": page_size,
                "search_params": payload
            }
        else:
            return {
                "success": False,
                "error": f"API请求失败，状态码: {response.status_code}",
                "message": response.text
            }
            
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"网络请求错误: {str(e)}"
        }
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"JSON解析错误: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"未知错误: {str(e)}"
        }


def analyze_properties_by_region_from_questionnaire(
    regions: str, 
    questionnaire_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    基于问卷数据按区域分析房源分布情况
    
    Args:
        regions: 区域代码，多个区域用逗号分隔
        questionnaire_data: 问卷数据字典
    
    Returns:
        包含区域分析结果的字典
    """
    try:
        # 提取并转换问卷数据
        min_price = questionnaire_data.get('budget_min')
        max_price = questionnaire_data.get('budget_max')
        room_type = questionnaire_data.get('room_type')
        target_school = questionnaire_data.get('target_school', 'University of New South Wales')
        
        # 调用底层分析函数
        return analyze_properties_by_region(
            regions=regions,
            min_price=min_price,
            max_price=max_price,
            target_school=target_school,
            room_type=room_type
        )
        
    except Exception as e:
        return {
            "success": False,
            "error": f"问卷数据处理错误: {str(e)}"
        }


def analyze_properties_by_region(
    regions: str,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    target_school: Optional[str] = None,
    room_type: Optional[str] = None,
    bedrooms: Optional[int] = None,
    bathrooms: Optional[int] = None
) -> Dict[str, Any]:
    """
    按区域分析房源分布情况
    
    Args:
        regions: 区域代码 (多个区域用逗号分隔)
        min_price: 最低价格
        max_price: 最高价格
        target_school: 目标学校
    
    Returns:
        包含区域分析结果的字典
    """
    try:
        region_list = [r.strip() for r in regions.split(',')]
        analysis_results = {}
        
        for region in region_list:
            # 搜索该区域的房源
            result = search_properties(
                regions=region,
                min_price=min_price,
                max_price=max_price,
                target_school=target_school,
                room_type=room_type,
                bedrooms=bedrooms,
                bathrooms=bathrooms,
                page_size=100  # 获取更多数据用于分析
            )
            
            if result["success"]:
                properties = result["properties"]
                
                # 分析房型分布
                room_types = {}
                total_properties = len(properties)
                
                for prop in properties:
                    bedroom_count = prop.get("bedroomCount", 0)
                    bathroom_count = prop.get("bathroomCount", 0)
                    room_key = f"{bedroom_count}室{bathroom_count}卫"
                    
                    if room_key not in room_types:
                        room_types[room_key] = {
                            "count": 0,
                            "prices": []
                        }
                    
                    room_types[room_key]["count"] += 1
                    price = prop.get("pricePerWeek")
                    if price:
                        room_types[room_key]["prices"].append(price)
                
                # 计算平均价格
                for room_data in room_types.values():
                    if room_data["prices"]:
                        room_data["avg_price"] = round(sum(room_data["prices"]) / len(room_data["prices"]), 2)
                    else:
                        room_data["avg_price"] = 0
                    del room_data["prices"]  # 移除原始价格数据
                
                analysis_results[region] = {
                    "total_properties": total_properties,
                    "room_types": room_types
                }
            else:
                analysis_results[region] = {
                    "error": result.get("error", "查询失败")
                }
        
        return {
            "success": True,
            "analysis_results": analysis_results
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"区域分析错误: {str(e)}"
        }


# 定义可用函数列表
AVAILABLE_FUNCTIONS = {
    "search_properties_from_questionnaire": {
        "function": search_properties_from_questionnaire,
        "description": "基于问卷数据搜索房源信息，自动处理问卷参数转换",
        "parameters": {
            "type": "object",
            "properties": {
                "questionnaire_data": {
                    "type": "object",
                    "description": "用户问卷数据，包含预算、房型、通勤时间等信息",
                    "properties": {
                        "budget_min": {"type": "integer", "description": "最低预算(AUD/周)"},
                        "budget_max": {"type": "integer", "description": "最高预算(AUD/周)"},
                        "room_type": {"type": "string", "description": "房型：Studio, 1 Bedroom, 2 Bedroom, 3+ Bedroom等"},
                        "commute_time": {"type": "string", "description": "通勤时间要求：15分钟以内, 30分钟以内, 45分钟以内, 1小时以内, 1小时以上, 没有要求"},
                        "target_school": {"type": "string", "description": "目标学校，默认为University of New South Wales"},
                        "includes_bills": {"type": "string", "description": "是否包含Bills：包含, 不包含, 不确定"},
                        "includes_furniture": {"type": "string", "description": "是否包含家具：包含, 不包含, 不确定"},
                        "total_budget": {"type": "integer", "description": "总开销预期(AUD/周)"},
                        "consider_sharing": {"type": "string", "description": "合租意愿：愿意考虑, 不考虑, 视情况而定"},
                        "move_in_date": {"type": "string", "description": "最早入住日期"},
                        "lease_duration": {"type": "string", "description": "期望租期：3个月, 6个月, 12个月等"},
                        "accept_premium": {"type": "string", "description": "接受高溢价：可以接受, 不能接受, 视房源质量而定"},
                        "accept_small_room": {"type": "string", "description": "接受小房间：可以接受, 不能接受, 视具体情况而定"}
                    }
                }
            },
            "required": ["questionnaire_data"]
        }
    },
    "search_properties": {
        "function": search_properties,
        "description": "搜索符合条件的房源信息（低级API，直接使用搜索参数）",
        "parameters": {
            "type": "object",
            "properties": {
                "min_price": {
                    "type": "integer",
                    "description": "最低价格 (AUD/周)"
                },
                "max_price": {
                    "type": "integer", 
                    "description": "最高价格 (AUD/周)"
                },
                "target_school": {
                    "type": "string",
                    "description": "目标学校名称，例如 'University of New South Wales'"
                },
                "min_commute_time": {
                    "type": "integer",
                    "description": "最短通勤时间 (分钟)"
                },
                "max_commute_time": {
                    "type": "integer",
                    "description": "最长通勤时间 (分钟)"
                },
                "regions": {
                    "type": "string",
                    "description": "区域代码，例如 'a', 'b', 'c' 等"
                },
                "room_type": {
                    "type": "string",
                    "description": "房型类型，例如 'studio', '1bedroom', '2bedroom', '3bedroom' 等，会自动转换为对应的卧室数量过滤"
                },
                "bedrooms": {
                    "type": "integer",
                    "description": "精确的卧室数量，例如 0(Studio), 1, 2, 3 等，优先级高于room_type"
                },
                "bathrooms": {
                    "type": "integer",
                    "description": "精确的卫生间数量，例如 1, 2, 3 等"
                },
                "page": {
                    "type": "integer",
                    "description": "页码，默认为1"
                },
                "page_size": {
                    "type": "integer",
                    "description": "每页数量，默认为10"
                }
            }
        }
    },
    "analyze_properties_by_region_from_questionnaire": {
        "function": analyze_properties_by_region_from_questionnaire,
        "description": "基于问卷数据按区域分析房源分布情况，包括房型统计和价格分析",
        "parameters": {
            "type": "object",
            "properties": {
                "regions": {
                    "type": "string",
                    "description": "区域代码，多个区域用逗号分隔，例如 'a,b,c'"
                },
                "questionnaire_data": {
                    "type": "object",
                    "description": "用户问卷数据，包含预算、房型等过滤条件",
                    "properties": {
                        "budget_min": {"type": "integer", "description": "最低预算(AUD/周)"},
                        "budget_max": {"type": "integer", "description": "最高预算(AUD/周)"},
                        "room_type": {"type": "string", "description": "房型偏好"},
                        "target_school": {"type": "string", "description": "目标学校"}
                    }
                }
            },
            "required": ["regions", "questionnaire_data"]
        }
    },
    "analyze_properties_by_region": {
        "function": analyze_properties_by_region,
        "description": "按区域分析房源分布情况，包括房型统计和价格分析（低级API）",
        "parameters": {
            "type": "object",
            "properties": {
                "regions": {
                    "type": "string",
                    "description": "区域代码，多个区域用逗号分隔，例如 'a,b,c'"
                },
                "min_price": {
                    "type": "integer",
                    "description": "最低价格过滤 (AUD/周)"
                },
                "max_price": {
                    "type": "integer",
                    "description": "最高价格过滤 (AUD/周)"
                },
                "target_school": {
                    "type": "string",
                    "description": "目标学校名称过滤"
                },
                "room_type": {
                    "type": "string",
                    "description": "房型类型过滤，例如 'studio', '1bedroom', '2bedroom' 等"
                },
                "bedrooms": {
                    "type": "integer",
                    "description": "卧室数量过滤"
                },
                "bathrooms": {
                    "type": "integer",
                    "description": "卫生间数量过滤"
                }
            },
            "required": ["regions"]
        }
    }
}


if __name__ == "__main__":
    # 测试代码
    print("测试房源搜索功能...")
    
    # 测试搜索函数
    result = search_properties(
        min_price=500,
        max_price=2000,
        target_school="University of New South Wales",
        regions="b",
        page=1,
        page_size=5
    )
    
    print("搜索结果:")
    print(f"成功: {result['success']}")
    if result['success']:
        print(f"找到房源数量: {result['count']}")
        print(f"搜索参数: {result['search_params']}")
        for i, prop in enumerate(result['properties'][:3], 1):
            print(f"  {i}. {prop.get('addressLine1', '')} {prop.get('addressLine2', '')}")
            print(f"     {prop.get('bedroomCount', 0)}室{prop.get('bathroomCount', 0)}卫, ${prop.get('pricePerWeek', 0)}/周")
    else:
        print(f"错误: {result['error']}")
