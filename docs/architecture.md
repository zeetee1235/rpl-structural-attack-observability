# 아키텍처 문서 (실험 워크플로우 + BRPL 구현)

## 1. 목적/범위
이 문서는 다음 두 가지를 설명한다.

1. **실험/시뮬레이션 워크플로우**: 시나리오 정의 → Cooja 실행 → 로그 수집 → 분석 → 리포트
2. **BRPL 구현 아키텍처**: RPL-Classic 기반 모듈 구성과 데이터 흐름

대상 코드는 현재 저장소 기준이며, 실제 실행은 Cooja headless 기준이다.

---

## 2. 실험 워크플로우 아키텍처

### 2.1 전체 흐름
1. **시나리오 정의**
   - `simulations/scenarios/*.csc`
   - 좌표/배치/노드 수/링크 모델 고정
2. **펌웨어 빌드**
   - `simulations/firmware/Makefile`
   - `BRPL=1` 시 BRPL 모드 활성화
3. **시뮬레이션 실행**
   - `scripts/run_experiments.sh`
   - 내부에서 `scripts/run_cooja_headless.py` 호출
4. **로그 수집**
   - run별 `*_COOJA.testlog` 저장
   - OBS 로그 포맷: `docs/logging_spec.md`
5. **분석**
   - `scripts/analyze_results.py`
   - PDR*, drop rate, CI 산출
6. **리포트**
   - `docs/experiments_result.md`

### 2.2 주요 구성요소

**A. 시나리오**
- 파일: `simulations/scenarios/*.csc`
- 역할: 토폴로지/노드 배치/무선 범위/프로파일 정의
- 핵심 시나리오:
  - A: Low Exposure
  - B: High Exposure (B(10), B(20))
  - C: High PD
  - D: 동일 APL/다른 BC

**B. 펌웨어**
- 파일: `simulations/firmware/rpl-node.c`
- 역할:
  - UDP 트래픽 발생
  - selective forwarding(공격자 모드)
  - OBS 로그 출력

**C. 실행기**
- 파일: `scripts/run_cooja_headless.py`
- 역할:
  - cooja.jar headless 실행
  - 환경 변수 주입 (ATTACK_RATE/ATTACKER_ID/ROOT_ID/BRPL)
  - `COOJA.testlog`를 run별 파일명으로 복사 저장

**D. 분석기**
- 파일: `scripts/analyze_results.py`
- 역할:
  - run별 testlog 파싱
  - PDR*, drop rate 계산
  - 시나리오×α 별 95% CI 계산

### 2.3 데이터 흐름(요약)
- 입력: `.csc` + `rpl-node.c` + 실험 파라미터
- 실행 산출물: `scenario_*.log`, `scenario_*_COOJA.testlog`
- 분석 산출물: `simulation_summary_*.csv`
- 최종 문서: `docs/experiments_result.md`

---

## 3. BRPL 구현 아키텍처 (RPL-Classic 기반)

### 3.1 모듈 구성
BRPL은 `contiki-ng-brpl`의 RPL-Classic 스택에 다음을 추가/확장한다.

**(1) Queue Manager**
- 파일: `contiki-ng-brpl/os/net/routing/rpl-classic/brpl-queue.c`
- 역할:
  - per-DAG 큐 길이 상태 관리
  - enqueue/dequeue/drop 카운터

**(2) DIO Queue Option**
- 파일: `contiki-ng-brpl/os/net/routing/rpl-classic/rpl-icmp6.c`
- 역할:
  - DIO에 큐 옵션(0xCE, 4 bytes, big-endian) 삽입
  - 이웃 큐 상태를 파싱하여 neighbor entry에 저장

**(3) BRPL OF/Rank Facade**
- 파일: `contiki-ng-brpl/os/net/routing/rpl-classic/rpl-brpl.c`
- 역할:
  - weight 계산: `w_{x,y} = θ * p_hat - (1-θ) * ΔQ_hat`
  - parent 선택: `argmin w`

**(4) QuickTheta / QuickBeta**
- 파일: `contiki-ng-brpl/os/net/routing/rpl-classic/rpl-brpl.c`
- 역할:
  - EWMA 큐 기반 θ 업데이트
  - 이웃 변화율 기반 β 업데이트

**(5) RPL DAG/Parent 확장**
- 파일: `contiki-ng-brpl/os/net/routing/rpl-classic/rpl.h`
- 역할:
  - parent entry에 queue 필드 추가
  - DAG에 BRPL 상태 추가

### 3.2 데이터 흐름(요약)
1. **큐 상태 업데이트**
   - 패킷 enqueue/dequeue 시 `brpl-queue` 상태 갱신
2. **DIO 송신**
   - `rpl-icmp6`에서 큐 옵션 삽입
3. **DIO 수신**
   - 이웃 큐 정보 업데이트
4. **QuickTheta/QuickBeta 계산**
   - 큐/이웃 변화 기반 θ, β 계산
5. **weight 계산 및 parent 선택**
   - `rpl-brpl`에서 weight 최소 parent 선택

### 3.3 주요 파라미터
- Queue max: 200 packets
- Queue scheduling: LIFO
- Queue full: drop new packet
- DIO interval: 512~1024ms
- MAC: CSMA / RDC: NULLRDC

---

## 4. 운영 시 주의사항
1. **PDR > 100% 이슈**
   - RX/TX 카운트 기준 불일치 가능
   - 보고서에는 PDR* (클리핑) 사용
2. **반복 실험 분산 0**
   - seed가 동일하거나 경로가 고정될 가능성
   - 필요 시 seed 분리 또는 트래픽 지터 강화

---

## 5. 관련 파일 요약
- 워크플로우
  - `scripts/run_experiments.sh`
  - `scripts/run_cooja_headless.py`
  - `scripts/analyze_results.py`
- 펌웨어
  - `simulations/firmware/rpl-node.c`
  - `simulations/firmware/Makefile`
- BRPL 구현
  - `contiki-ng-brpl/os/net/routing/rpl-classic/rpl-brpl.c`
  - `contiki-ng-brpl/os/net/routing/rpl-classic/brpl-queue.c`
  - `contiki-ng-brpl/os/net/routing/rpl-classic/rpl-icmp6.c`
  - `contiki-ng-brpl/os/net/routing/rpl-classic/rpl.h`
**End Patch"}}
