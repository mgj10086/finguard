#!/usr/bin/env python
"""
种子数据脚本

插入示例法规和违规案例数据，便于开发测试。
"""

import asyncio
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.core.database import async_session_factory, init_db
from backend.models.regulation import (
    Chapter, Clause, Regulation, RegulationSource, RegulationStatus, ViolationCase,
)


SAMPLE_REGULATIONS = [
    {
        "title": "商业银行信息披露办法",
        "short_title": "信息披露办法",
        "source": RegulationSource.CBIRC,
        "doc_number": "银监会令2024年第1号",
        "status": RegulationStatus.ACTIVE,
        "publish_date": date(2024, 1, 15),
        "effective_date": date(2024, 3, 1),
        "summary": "规范商业银行信息披露行为，保护存款人和相关利益人的合法权益。",
        "chapters": [
            {
                "title": "总则",
                "order_num": 1,
                "clauses": [
                    {
                        "order_num": "第一条",
                        "content": "为规范商业银行信息披露行为，保护存款人和其他客户的合法权益，促进银行业稳健经营，根据《中华人民共和国银行业监督管理法》《中华人民共和国商业银行法》等法律法规，制定本办法。",
                        "keywords": "目的,依据,商业银行,信息披露",
                        "risk_level": "low",
                    },
                    {
                        "order_num": "第二条",
                        "content": "本办法适用于在中华人民共和国境内依法设立的商业银行。外国银行分行参照适用本办法。",
                        "keywords": "适用范围,商业银行,外国银行分行",
                        "risk_level": "low",
                    },
                    {
                        "order_num": "第三条",
                        "content": "商业银行应当按照本办法的规定，真实、准确、完整、及时地披露信息。披露的信息应当易于理解，方便信息使用者获取。",
                        "keywords": "真实性,准确性,完整性,及时性,披露要求",
                        "risk_level": "high",
                    },
                ],
            },
            {
                "title": "信息披露内容",
                "order_num": 2,
                "clauses": [
                    {
                        "order_num": "第七条",
                        "content": "商业银行应当披露年度报告，包括财务报告、风险管理信息、公司治理信息、年度重大事项等。",
                        "keywords": "年度报告,财务报告,风险管理,公司治理",
                        "risk_level": "high",
                    },
                    {
                        "order_num": "第八条",
                        "content": "商业银行披露的财务报告应当经具有证券、期货相关业务资格的会计师事务所审计。",
                        "keywords": "财务报告,审计,会计师事务所",
                        "risk_level": "high",
                    },
                    {
                        "order_num": "第十二条",
                        "content": "商业银行应当在每个会计年度结束后的四个月内披露年度报告。因特殊原因不能按时披露的，应当提前向银行业监督管理机构报告并说明原因。",
                        "keywords": "披露时限,年度报告,会计年度,延期报告",
                        "risk_level": "medium",
                    },
                ],
            },
        ],
    },
    {
        "title": "商业银行金融资产风险分类办法",
        "short_title": "风险分类办法",
        "source": RegulationSource.CBIRC,
        "doc_number": "银监会令2023年第3号",
        "status": RegulationStatus.ACTIVE,
        "publish_date": date(2023, 7, 1),
        "effective_date": date(2023, 9, 1),
        "summary": "规范商业银行金融资产风险分类，准确识别和计量信用风险。",
        "chapters": [
            {
                "title": "总则",
                "order_num": 1,
                "clauses": [
                    {
                        "order_num": "第三条",
                        "content": "商业银行应当按照本办法的规定，对金融资产进行风险分类。风险分类应当真实、准确地反映金融资产的信用风险水平。",
                        "keywords": "风险分类,金融资产,信用风险",
                        "risk_level": "high",
                    },
                    {
                        "order_num": "第五条",
                        "content": "金融资产风险分类分为正常类、关注类、次级类、可疑类和损失类五级。后三类合称为不良资产。",
                        "keywords": "五级分类,正常类,关注类,次级类,可疑类,损失类,不良资产",
                        "risk_level": "high",
                    },
                ],
            },
        ],
    },
]

SAMPLE_VIOLATION_CASES = [
    {
        "clause_order_num": "第三条",
        "title": "某商业银行信息披露不真实被处罚案",
        "description": "某银行在年度报告中虚增利润，未如实披露不良贷款率，被监管部门发现并处罚。",
        "penalty": "罚款500万元，责令改正，对相关责任人给予警告",
        "penalty_amount": "500万",
        "year": 2023,
        "institution_name": "某股份制商业银行",
    },
    {
        "clause_order_num": "第十二条",
        "title": "某城商行年度报告延期披露案",
        "description": "某城市商业银行未在规定期限内披露年度报告，也未向监管部门报告延期原因。",
        "penalty": "罚款50万元，责令限期披露",
        "penalty_amount": "50万",
        "year": 2023,
        "institution_name": "某城市商业银行",
    },
]


async def main():
    print("=== FinGuard 种子数据插入 ===")
    await init_db()

    async with async_session_factory() as session:
        # 插入法规
        for reg_data in SAMPLE_REGULATIONS:
            chapters_data = reg_data.pop("chapters")
            reg = Regulation(**reg_data)
            session.add(reg)
            await session.flush()

            for ch_data in chapters_data:
                clauses_data = ch_data.pop("clauses")
                chapter = Chapter(regulation_id=reg.id, **ch_data)
                session.add(chapter)
                await session.flush()

                for cl_data in clauses_data:
                    clause = Clause(chapter_id=chapter.id, **cl_data)
                    session.add(clause)
                    await session.flush()

            print(f"  ✅ 法规: {reg.short_title} ({len(chapters_data)}章)")

        # 插入违规案例（关联到第一个条款）
        first_clause = None
        for clause_order_num in [c["clause_order_num"] for c in SAMPLE_VIOLATION_CASES]:
            from sqlalchemy import select
            from sqlalchemy.orm import selectinload
            # 找到对应条款
            stmt = select(Clause).where(Clause.order_num == clause_order_num).limit(1)
            result = await session.execute(stmt)
            clause = result.scalar_one_or_none()

        for case_data in SAMPLE_VIOLATION_CASES:
            clause_order = case_data.pop("clause_order_num")
            # 简单关联到匹配的条款
            stmt = select(Clause).where(Clause.order_num == clause_order).limit(1)
            result = await session.execute(stmt)
            clause = result.scalar_one_or_none()
            if clause:
                case_data["clause_id"] = clause.id

            case = ViolationCase(**case_data)
            session.add(case)
            await session.flush()
            print(f"  ✅ 违规案例: {case.title}")

        await session.commit()

    print("✅ 种子数据插入完成")


if __name__ == "__main__":
    asyncio.run(main())
