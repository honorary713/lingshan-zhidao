TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_registration",
            "description": "查询新生报到入学相关信息：报到流程、必带材料、学费/住宿费缴纳、一卡通领取激活、校园网开通、军训安排、入学体检等。",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "新生的原始问题",
                    },
                },
                "required": ["question"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_living",
            "description": "查询住宿与餐饮等生活服务：宿舍水电空调、食堂餐厅、快递驿站、校内商超、洗浴开水、门禁报修等。",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "新生的原始问题",
                    },
                },
                "required": ["question"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_academics",
            "description": "查询学习与教务：课程、选课、学分、图书馆借阅与自习、教材、考试、学籍、培养方案、转专业等。",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "新生的原始问题",
                    },
                },
                "required": ["question"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_financial_aid",
            "description": "查询奖助学金与资助：奖学金、助学金、生源地助学贷款、勤工助学、绿色通道、困难补助等政策与办理。",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "新生的原始问题",
                    },
                },
                "required": ["question"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_campus_life",
            "description": "查询校园生活：社团招新、体育活动、讲座比赛、志愿服务（第二课堂）、心理咨询、校医院就医、就业招聘等。",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "新生的原始问题",
                    },
                },
                "required": ["question"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_service",
            "description": "查询办事服务与数字校园：在读/成绩/住宿证明开具、请假销假、一卡通充值挂失补卡、校园网故障、VPN、正版软件、邮箱、统一身份认证。",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "新生的原始问题",
                    },
                },
                "required": ["question"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_safety",
            "description": "查询安全与防骗：电信诈骗常见套路、消防安全、宿舍用电安全、紧急联系方式、防推销防传销、校园贷风险。",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "新生的原始问题",
                    },
                },
                "required": ["question"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_overview",
            "description": "查询学校概况与地标：学校历史、校区分布、校训精神、地址、双一流/211 属性、主要建筑与功能。",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "新生的原始问题",
                    },
                },
                "required": ["question"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_general",
            "description": "通用检索：不限定分类，在全量校园知识库中检索，用于无法归入上述分类的综合性问题。",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "新生的原始问题",
                    },
                },
                "required": ["question"],
            },
        },
    },
]
