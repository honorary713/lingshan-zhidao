// ============================================================
// 校园智导 · 新生报到动线
// 坐标采用百分比（pctX/pctY），便于根据实拍/底图微调位置
// viewBox 与 campus_map.jpg 实际像素一致（1215×806）
// ============================================================

export const GUIDE_VIEWBOX = { w: 1215, h: 806 }

// 占位符：后续把实拍照片放到 frontend/public/images/campus/ 下，
// 并将 img 字段改为例如 '/images/campus/nanmen.jpg'
export const GUIDE_SPOTS = [
  {
    id: 1,
    no: '01',
    name: '南门',
    pctX: 50, pctY: 86,
    walkFromPrev: null,
    brief: '校园的迎宾门户，见证学子的到来与启程，承载着对大学生活的期待与回忆。',
    img: '/images/campus/nanmen.jpg',
    tip: '建议实地拍摄：校门全景、报到日的引导牌',
  },
  {
    id: 2,
    no: '02',
    name: '图书馆',
    pctX: 40, pctY: 46,
    walkFromPrev: '步行约 5 分钟',
    brief: '书香汇聚的知识殿堂，是静心阅读、探索知识与潜心学习的好去处。',
    img: '/images/campus/tushuguan.jpg',
    tip: '建议实地拍摄：图书馆外观、大厅、自习区',
  },
  {
    id: 3,
    no: '03',
    name: '荟萃广场',
    pctX: 26, pctY: 38,
    walkFromPrev: '步行约 3 分钟',
    brief: '校园生活的开放空间，青春在这里相聚，活力与朝气在这里绽放。',
    img: '/images/campus/huicui.jpg',
    tip: '建议实地拍摄：广场全景、周边食堂/宿舍楼',
  },
  {
    id: 4,
    no: '04',
    name: '行政楼',
    pctX: 52, pctY: 34,
    walkFromPrev: '步行约 5 分钟',
    brief: '学校日常管理与服务的重要场所，为校园有序运行提供保障。',
    img: '/images/campus/xingzheng.jpg',
    tip: '建议实地拍摄：行政楼外观、办事大厅入口',
  },
  {
    id: 5,
    no: '05',
    name: '体育馆',
    pctX: 12, pctY: 16,
    walkFromPrev: '步行约 8 分钟',
    brief: '挥洒汗水、展现风采的运动空间，记录着拼搏的身影与团结的力量。',
    img: '/images/campus/tiyuguan.jpg',
    tip: '建议实地拍摄：体育馆外观、内部运动场地',
  },
  {
    id: 6,
    no: '06',
    name: '就业中心 · 报告厅',
    pctX: 42, pctY: 64,
    walkFromPrev: '步行约 10 分钟',
    brief: '连接校园与未来的平台，也是交流思想、拓展视野的重要场所。',
    img: null,
    tip: '建议实地拍摄：就业中心入口、报告厅内景',
  },
  {
    id: 7,
    no: '07',
    name: '南教楼',
    pctX: 58, pctY: 58,
    walkFromPrev: '步行约 4 分钟',
    brief: '传授知识、启迪思考的课堂阵地，陪伴学子度过充实的求学时光。',
    img: null,
    tip: '建议实地拍摄：教学楼外观、典型教室',
  },
  {
    id: 8,
    no: '08',
    name: '图书馆东馆 · 校史馆',
    pctX: 80, pctY: 42,
    walkFromPrev: '步行约 6 分钟',
    brief: '在书香中回望学校的发展历程，感受石大精神与薪火相传的文化底蕴。',
    img: '/images/campus/xiaoshiguan.jpg',
    tip: '建议实地拍摄：东馆外观、校史馆内景',
  },
]

export const GUIDE_ROUTE_NAME = '校园智导 · 新生报到动线'

// 相邻两点步行时长标签（中点定位用）
export const GUIDE_SEGMENTS = GUIDE_SPOTS.slice(1).map((spot, i) => {
  const prev = GUIDE_SPOTS[i]
  return {
    from: prev,
    to: spot,
    label: spot.walkFromPrev,
    mx: (prev.pctX + spot.pctX) / 2 * GUIDE_VIEWBOX.w / 100,
    my: (prev.pctY + spot.pctY) / 2 * GUIDE_VIEWBOX.h / 100,
  }
})
