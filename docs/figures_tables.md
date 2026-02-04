# Figures and Tables Guide

이 문서는 생성된 Figure/Table의 **의미, 사용 데이터, 논문 내 삽입 위치**를 요약한다.

---

## Figures

### Fig.1 — Experimental Workflow Diagram
- 파일: `docs/figures/fig1_workflow.pdf`, `docs/figures/fig1_workflow.png`
- 목적: 실험 파이프라인의 **재현성/자동화** 강조
- 데이터: 없음(개념도)
- 삽입 위치: Section 3.1 (Experimental Methodology 서두)

### Fig.2 — Scenario Topologies (A/B/C/D)
- 파일: `docs/figures/fig2_topologies.pdf`, `docs/figures/fig2_topologies.png`
- 목적: 구조적 차이 시각화
- 데이터: `simulations/scenarios/SCENARIO_COORDINATES.md` 좌표
- 삽입 위치: Section 3.2 (Scenarios)

### Fig.3 — BRPL Implementation Architecture
- 파일: `docs/figures/fig3_brpl_architecture.pdf`, `docs/figures/fig3_brpl_architecture.png`
- 목적: 구현 구조(Queue → DIO → QuickTheta/Beta → Parent Selection) 요약
- 데이터: 없음(구조도)
- 삽입 위치: Section 4 (BRPL Implementation 서두)

### Fig.4 — Parent Selection Model (Conceptual)
- 파일: `docs/figures/fig4_parent_selection_model.pdf`, `docs/figures/fig4_parent_selection_model.png`
- 목적: θ 변화에 따른 **RPL/Backpressure 가중** 직관화
- 데이터: 없음(개념도)
- 삽입 위치: Section 4.4 (Parent Selection 설명 직후)

### Fig.5 — PDR* vs α (Scenario B)
- 파일: `docs/figures/fig5_pdr_vs_alpha_b.pdf`, `docs/figures/fig5_pdr_vs_alpha_b.png`
- 목적: **핵심 결과** (High Exposure에서 α 증가 시 PDR* 급락)
- 데이터: `simulations/output/simulation_summary_20260204_230503.csv`
- 삽입 위치: Section 5.2.1 (High Exposure)

### Fig.6 — PDR* vs α (A/B/C/D 비교)
- 파일: `docs/figures/fig6_pdr_vs_alpha_abcd.pdf`, `docs/figures/fig6_pdr_vs_alpha_abcd.png`
- 목적: 구조별 관측 가능성 비교
- 데이터: `simulations/output/simulation_summary_20260204_230503.csv`
- 삽입 위치: Section 5.2 (결과 비교 서두)

### Fig.7 — Exposure vs PDR*
- 파일: `docs/figures/fig7_exposure_vs_pdr.pdf`, `docs/figures/fig7_exposure_vs_pdr.png`
- 목적: **Exposure가 관측 가능성을 지배**함을 시각화
- 데이터: `exposure_e1_prime` (summary CSV)
- 삽입 위치: Section 6.1 (Discussion 시작)

### Fig.8 — Scale Effect (10 vs 20)
- 파일: `docs/figures/fig8_scale_effect.pdf`, `docs/figures/fig8_scale_effect.png`
- 목적: 노드 수 증가 시 관측 영향 확인
- 데이터: `simulations/output/simulation_summary_20260204_230503.csv`
- 삽입 위치: Section 5.3 (Scale Effect)

### Fig.9 — Parent Composition Breakdown
- 파일: `docs/figures/fig9_parent_composition.pdf`, `docs/figures/fig9_parent_composition.png`
- 목적: 결과 원인 설명(Direct / via attacker / via relay)
- 데이터: 각 run의 `*_COOJA.testlog` 내 `ev=PARENT` 로그
- 삽입 위치: Section 6.2 (Why detection fails)

### Fig.10 — Observability Summary Heatmap
- 파일: `docs/figures/fig10_observability_heatmap.pdf`, `docs/figures/fig10_observability_heatmap.png`
- 목적: 전체 결과 요약(시나리오×α)
- 데이터: `simulations/output/simulation_summary_20260204_230503.csv`
- 삽입 위치: Discussion 마지막 or Conclusion 직전

---

## Tables

### Table 1 — Simulation Parameters
- 파일: `docs/tables/table1_sim_params.csv`
- 목적: 실험 환경/파라미터 요약
- 삽입 위치: Section 3 (Experimental Setup)

### Table 2 — Mean PDR* ± 95% CI
- 파일: `docs/tables/table2_pdr_ci.csv`
- 목적: 시나리오×α별 평균과 신뢰구간
- 삽입 위치: Section 5 (Results)

---

## 재생성 방법

```bash
Rscript scripts/generate_figures.R simulations/output/simulation_summary_20260204_230503.csv docs/figures
```

생성 산출물:
- Figures: `docs/figures/*.pdf`, `docs/figures/*.png`
- Tables: `docs/tables/table1_sim_params.csv`, `docs/tables/table2_pdr_ci.csv`
