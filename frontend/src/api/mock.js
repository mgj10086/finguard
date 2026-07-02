/**
 * FinGuard Mock 数据层
 *
 * 当后端不可用时，自动使用本模块提供模拟数据，
 * 确保前端可独立运行和演示。
 */

// ========== 模拟数据 ==========

const MOCK_REVIEWS = [
  {
    id: 1,
    uuid: 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
    title: '审核: 2024年度信息披露报告',
    document_id: 1,
    status: 'completed',
    compliance_score: 72.5,
    total_findings: 5,
    critical_count: 1,
    high_count: 2,
    medium_count: 1,
    low_count: 1,
    needs_human_review: true,
    human_review_reason: '包含 1 项重大违规，需人工确认',
    summary: '经审核，该信息披露报告整体合规性尚可。主要发现：财务报表附注中关联交易披露不完整（重大违规），风险加权资产计量方法描述与现行法规存在偏差（高风险），以及董事会构成信息披露存在时效性问题。建议对上述问题逐一整改，重点关注关联交易的完整披露。',
    business_type: '信息披露',
    findings: [
      {
        id: 1,
        severity: 'critical',
        title: '关联交易披露不完整',
        description: '年度报告第3.2节中，关联交易部分仅披露了与主要股东的关联交易，未披露与子公司、联营企业之间的关联交易情况，违反《商业银行信息披露办法》关于关联交易完整披露的要求。',
        regulation_cited: '《商业银行信息披露办法》第七条',
        source_text: '3.2 关联交易\n报告期内，本行与主要股东之间的关联交易总额为12.5亿元...',
        reasoning: '经比对法规第七条"商业银行应当披露关联交易的相关信息"，此处的关联交易涵盖全部关联方。报告仅披露与主要股东的关联交易，属于重大遗漏。',
        suggestion: '补充披露与子公司、联营企业、关键管理人员及其他关联方的交易情况，确保完整性。',
        source_section: '3.2 关联交易',
      },
      {
        id: 2,
        severity: 'high',
        title: '风险加权资产计量方法描述不准确',
        description: '报告中描述风险加权资产计量采用权重法，但实际资产结构包含大量复杂衍生品，根据法规应采用内部评级法或至少披露两种方法的差异。',
        regulation_cited: '《商业银行金融资产风险分类办法》第三条',
        source_text: '本行采用权重法计量风险加权资产...',
        reasoning: '依据法规第三条要求，金融资产风险分类应当真实、准确地反映信用风险水平。权重法对复杂衍生品的风险敏感度不足。',
        suggestion: '建议补充采用内部评级法计量的对比数据，或说明使用权重法的合理性。',
        source_section: '4.1 风险管理',
      },
      {
        id: 3,
        severity: 'high',
        title: '不良贷款五级分类指标未达披露标准',
        description: '报告中披露的不良贷款率与核心监管指标存在偏差，次级类贷款占比异常升高但未做特别说明。',
        regulation_cited: '《商业银行金融资产风险分类办法》第五条',
        source_text: '不良贷款率 2.15%，较上年上升0.3个百分点...',
        reasoning: '不良贷款率上升需分析原因，特别是次级类、可疑类、损失类的具体分布和变动原因。当前披露过于笼统。',
        suggestion: '补充五级分类的具体分布、变动原因及后续管理措施。',
        source_section: '4.2 信用风险',
      },
      {
        id: 4,
        severity: 'medium',
        title: '公司治理信息披露存在滞后',
        description: '董事会成员变更信息在公司治理章节中未及时更新，部分董事任期已届满但仍在任。',
        regulation_cited: '《商业银行信息披露办法》第七条',
        source_text: '公司治理...董事会由9名董事组成...',
        reasoning: '公司治理信息应当反映报告期末的实际情况，包括董事任职期限和变更情况。',
        suggestion: '更新董事会构成信息，说明董事任期的起止时间及变更情况。',
        source_section: '5.1 公司治理',
      },
      {
        id: 5,
        severity: 'low',
        title: '部分财务数据口径说明不清晰',
        description: '部分财务数据的计算口径和调整依据未做充分脚注说明，可能影响信息使用者的理解。',
        regulation_cited: '《商业银行信息披露办法》第三条',
        source_text: '调整后净利润 85.6亿元...',
        reasoning: '法规第三条要求披露的信息应当易于理解。调整项明细缺失降低了可理解性。',
        suggestion: '补充财务数据调整项的明细和计算口径说明。',
        source_section: '2.1 主要财务指标',
      },
    ],
    created_at: '2026-06-28T10:30:00+08:00',
    completed_at: '2026-06-28T11:02:00+08:00',
  },
  {
    id: 2,
    uuid: 'b2c3d4e5-f6a7-8901-bcde-f12345678901',
    title: '审核: 2024年二季度风险自评表',
    document_id: 2,
    status: 'completed',
    compliance_score: 88.0,
    total_findings: 2,
    critical_count: 0,
    high_count: 1,
    medium_count: 1,
    low_count: 0,
    needs_human_review: false,
    summary: '风险自评表整体合规性良好。存在流动性风险指标计算口径偏差（高风险），以及操作风险事件分类不够细化两项问题，建议优化后即可通过。',
    business_type: '风险自评',
    findings: [
      {
        id: 6,
        severity: 'high',
        title: '流动性覆盖率计算口径偏差',
        description: '流动性覆盖率（LCR）计算中，合格优质流动性资产（HQLA）的认定范围偏宽，纳入了部分不符合监管定义的资产。',
        regulation_cited: '《商业银行流动性风险管理办法》',
        source_text: '合格优质流动性资产包括：现金、国债、政策性金融债、AA级以上信用债...',
        reasoning: 'AA级以上信用债在压力情境下的流动性可能不足，不应全额计入HQLA。',
        suggestion: '按照监管规定重新认定HQLA范围，剔除不符合条件的资产。',
        source_section: '2.3 流动性风险',
      },
      {
        id: 7,
        severity: 'medium',
        title: '操作风险事件分类不够细化',
        description: '操作风险事件仅按大类归集，未按照《操作风险管理指引》要求细分为7类事件类型。',
        regulation_cited: '《商业银行操作风险管理指引》',
        source_text: '操作风险损失合计：1,250万元...',
        reasoning: '过于笼统的分类不利于精准识别风险点和制定管控措施。',
        suggestion: '按内外部欺诈、就业制度、客户产品、实物资产、业务中断、执行交割等七类细化分类。',
        source_section: '2.5 操作风险',
      },
    ],
    created_at: '2026-06-30T14:00:00+08:00',
    completed_at: '2026-06-30T14:25:00+08:00',
  },
  {
    id: 3,
    uuid: 'c3d4e5f6-a7b8-9012-cdef-123456789012',
    title: '审核: 2024年度资本充足率报告',
    document_id: 3,
    status: 'pending',
    compliance_score: null,
    total_findings: 0,
    needs_human_review: false,
    business_type: '年度报告',
    created_at: '2026-07-01T09:00:00+08:00',
  },
]

const MOCK_DOCUMENTS = [
  { id: 1, filename: '2024年度信息披露报告.pdf', file_type: 'pdf', doc_type: 'disclosure_report', status: 'parsed', page_count: 128, file_size: 4_200_000, uploaded_by: '合规部-张三', created_at: '2026-06-27T10:00:00+08:00' },
  { id: 2, filename: '2024Q2风险自评表.docx', file_type: 'docx', doc_type: 'risk_self_assessment', status: 'parsed', page_count: 45, file_size: 1_800_000, uploaded_by: '风险部-李四', created_at: '2026-06-29T11:00:00+08:00' },
  { id: 3, filename: '2024资本充足率报告.pdf', file_type: 'pdf', doc_type: 'annual_report', status: 'parsed', page_count: 88, file_size: 3_100_000, uploaded_by: '合规部-张三', created_at: '2026-07-01T08:30:00+08:00' },
  { id: 4, filename: '内部控制自我评估报告.docx', file_type: 'docx', doc_type: 'other', status: 'uploaded', page_count: null, file_size: 2_500_000, uploaded_by: '内审部-王五', created_at: '2026-07-02T09:15:00+08:00' },
]

const MOCK_REGULATIONS = [
  { id: 1, short_title: '商业银行信息披露办法', title: '商业银行信息披露办法', source: 'cbirc', doc_number: '银监会令2024年第1号', status: 'active', effective_date: '2024-03-01', publish_date: '2024-01-15' },
  { id: 2, short_title: '金融资产风险分类办法', title: '商业银行金融资产风险分类办法', source: 'cbirc', doc_number: '银监会令2023年第3号', status: 'active', effective_date: '2023-09-01', publish_date: '2023-07-01' },
  { id: 3, short_title: '流动性风险管理办法', title: '商业银行流动性风险管理办法', source: 'cbirc', doc_number: '银监会令2023年第5号', status: 'active', effective_date: '2024-01-01', publish_date: '2023-10-15' },
  { id: 4, short_title: '操作风险管理指引', title: '商业银行操作风险管理指引', source: 'cbirc', doc_number: '银监发2023年28号', status: 'active', effective_date: '2023-12-01', publish_date: '2023-11-01' },
]

// ========== Mock API 响应 ==========

function mockResponse(data, delay = 300) {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        code: 200,
        message: 'success',
        data,
        timestamp: new Date().toISOString(),
      })
    }, delay)
  })
}

export const mockApis = {
  // 文档
  uploadDocument(formData) {
    const file = formData.get('file')
    return mockResponse({
      id: Date.now(),
      filename: file.name,
      status: 'parsed',
    })
  },
  listDocuments(params) {
    let items = [...MOCK_DOCUMENTS]
    if (params?.status) items = items.filter(d => d.status === params.status)
    return mockResponse({
      items,
      total: items.length,
      page: params?.page || 1,
      page_size: params?.page_size || 20,
    })
  },
  getDocument(id) {
    const doc = MOCK_DOCUMENTS.find(d => d.id === Number(id))
    return mockResponse(doc || MOCK_DOCUMENTS[0])
  },

  // 审核
  createReview(data) {
    return mockResponse({ id: Date.now(), uuid: crypto.randomUUID(), title: data.title || '新审核任务', status: 'pending' })
  },
  startReview(id) {
    const review = MOCK_REVIEWS.find(r => r.id === Number(id))
    return mockResponse({ id: Number(id), status: 'completed', compliance_score: review?.compliance_score || 85, total_findings: review?.findings?.length || 0, summary: review?.summary || '审核完成', needs_human_review: review?.needs_human_review || false })
  },
  listReviews(params) {
    let items = [...MOCK_REVIEWS]
    if (params?.status) items = items.filter(r => r.status === params.status)
    return mockResponse({
      items,
      total: items.length,
      page: params?.page || 1,
      page_size: params?.page_size || 20,
    })
  },
  getReview(id) {
    const review = MOCK_REVIEWS.find(r => r.id === Number(id)) || MOCK_REVIEWS[0]
    return mockResponse(review)
  },
  confirmReview(id, action, comment) {
    return mockResponse({ id: Number(id), status: action === 'approve' ? 'completed' : 'rejected' })
  },

  // 法规知识库
  uploadRegulation(formData) {
    return mockResponse({ id: Date.now(), title: formData.get('file')?.name || '新法规', source: formData.get('source'), index_stats: { documents: 1, nodes: 23 } })
  },
  listRegulations(params) {
    return mockResponse({ items: MOCK_REGULATIONS, total: MOCK_REGULATIONS.length })
  },
  searchRegulations(query, top_k = 5) {
    const results = [
      { content: '商业银行应当按照本办法的规定，真实、准确、完整、及时地披露信息。披露的信息应当易于理解，方便信息使用者获取。', score: 0.92, metadata: { regulation: '信息披露办法', clause: '第三条' } },
      { content: '商业银行应当披露年度报告，包括财务报告、风险管理信息、公司治理信息、年度重大事项等。', score: 0.88, metadata: { regulation: '信息披露办法', clause: '第七条' } },
      { content: '商业银行披露的财务报告应当经具有证券、期货相关业务资格的会计师事务所审计。', score: 0.85, metadata: { regulation: '信息披露办法', clause: '第八条' } },
      { content: '商业银行应当在每个会计年度结束后的四个月内披露年度报告。因特殊原因不能按时披露的，应当提前向银行业监督管理机构报告并说明原因。', score: 0.82, metadata: { regulation: '信息披露办法', clause: '第十二条' } },
      { content: '商业银行应当按照本办法的规定，对金融资产进行风险分类。风险分类应当真实、准确地反映金融资产的信用风险水平。', score: 0.79, metadata: { regulation: '风险分类办法', clause: '第三条' } },
    ].slice(0, top_k)
    return mockResponse({ query, results })
  },
}
