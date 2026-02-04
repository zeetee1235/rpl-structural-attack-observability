# ATTACK_RATE 적용 가이드

## 문제

ATTACK_RATE가 0.00으로 출력되어 공격률이 실제로 적용되지 않는 문제가 있었습니다.

## 해결 방법

### 1. .csc 파일 수정

모든 시나리오 파일(`.csc`)의 `<commands>` 태그를 다음과 같이 수정했습니다:

```xml
<commands>make clean TARGET=cooja &amp;&amp; make rpl-node.cooja TARGET=cooja ATTACKER_ID=$${ATTACKER_ID:-6} ATTACK_RATE=$${ATTACK_RATE:-0.0} ROOT_ID=$${ROOT_ID:-1}</commands>
```

**핵심 변경사항:**
- `make clean`을 추가하여 캐시된 빌드 제거
- `$${VARIABLE:-default}` 문법으로 환경 변수 전달
- XML에서 `&amp;&amp;`는 `&&`로 해석됨

### 2. 환경 변수 전달

`run_cooja_headless.py`는 다음 환경 변수들을 설정합니다:

```python
env["ATTACKER_ID"] = str(attacker_id)
env["ATTACK_RATE"] = str(attack_rate)
env["ROOT_ID"] = str(root_id)
```

이 환경 변수들이 Cooja 실행 시 make 명령어로 전달됩니다.

### 3. Firmware에서 값 사용

`rpl-node.c`에서:

```c
#ifndef ATTACK_RATE
#define ATTACK_RATE 0.0
#endif

// ...

printf("OBS ts=%lu node=%u ev=ATTACK_START rate=%.2f\n",
       (unsigned long)now_ms(),
       (unsigned)ATTACKER_ID,
       (double)ATTACK_RATE);
```

## 검증 방법

### 1. Firmware 빌드 테스트

```bash
./scripts/test_firmware_build.sh
```

이 스크립트는:
- 여러 ATTACK_RATE 값으로 firmware를 빌드
- 각 빌드가 성공하는지 확인
- 바이너리에서 관련 심볼 검색

### 2. 실제 시뮬레이션 테스트

```bash
./scripts/test_attack_rate.sh
```

이 스크립트는:
- ATTACK_RATE=0.6으로 시뮬레이션 실행
- 로그에서 DATA_DROP 이벤트 확인
- 실제 drop rate 계산

**예상 출력:**

```
Searching for ATTACK_RATE mentions in logs...
OBS ts=15000 node=6 ev=ATTACK_START rate=0.60

Total DATA_DROP events: 45
Total DATA_FWD events: 30
Expected drop rate: 0.6
Actual drop rate: 0.60
```

### 3. 로그 확인

시뮬레이션 후 `COOJA.testlog`를 확인:

```bash
# ATTACK_START 이벤트에서 rate 확인
grep "ATTACK_START" simulations/output/COOJA.testlog

# DROP/FWD 비율 계산
grep -c "DATA_DROP" simulations/output/COOJA.testlog
grep -c "DATA_FWD" simulations/output/COOJA.testlog
```

## 문제 해결

### ATTACK_RATE가 여전히 0.0인 경우

1. **환경 변수 확인:**
   ```bash
   # 시뮬레이션 실행 시 환경 변수 출력 확인
   python3 scripts/run_cooja_headless.py ... --attack-rate 0.6
   # 출력에서 "ATTACK_RATE=0.6" 확인
   ```

2. **빌드 캐시 문제:**
   ```bash
   # firmware 디렉토리 수동 clean
   cd simulations/firmware
   make clean TARGET=cooja
   rm -rf build/
   ```

3. **Cooja 로그 확인:**
   ```bash
   # Cooja의 컴파일 로그에서 CFLAGS 확인
   grep "CFLAGS" simulations/output/*.log | grep ATTACK_RATE
   ```

### DATA_DROP이 발생하지 않는 경우

1. **토폴로지 확인:**
   - Attacker 노드(ID 6)가 cut-vertex인지 확인
   - 다른 노드들이 attacker를 통해 root에 도달하는지 확인

2. **라우팅 확인:**
   ```bash
   # PARENT 이벤트 확인
   grep "ev=PARENT" simulations/output/COOJA.testlog
   # Node들이 attacker를 parent로 선택하는지 확인
   ```

3. **시뮬레이션 시간:**
   - 충분한 시간(최소 5분) 실행
   - 네트워크가 안정화될 때까지 대기

## 추가 테스트

### 다양한 ATTACK_RATE로 실험

```bash
for rate in 0.0 0.2 0.4 0.6 0.8 1.0; do
  echo "Testing with ATTACK_RATE=$rate"
  python3 scripts/run_cooja_headless.py \
    --cooja-path /home/dev/contiki-ng/tools/cooja \
    --contiki-path contiki-ng-brpl \
    --simulation simulations/scenarios/scenario_b_high_exposure_20.csc \
    --output-dir simulations/output \
    --timeout 120 \
    --attacker-id 6 \
    --attack-rate $rate \
    --routing brpl
  
  # 결과 분석
  python3 scripts/parse_cooja_logs.py \
    --log-file simulations/output/COOJA.testlog \
    --output-dir data \
    --scenario "scenario_b_rate_${rate}" \
    --scenario-file simulations/scenarios/scenario_b_high_exposure_20.csc
done
```

## 참고사항

- `.csc` 파일의 `$${VAR:-default}` 문법은 Bash 문법
- XML에서 `&`는 `&amp;`로 이스케이프 필요
- `make clean`은 빌드 시간을 늘리지만 일관성 보장
- ATTACK_RATE는 컴파일 타임 상수이므로 시뮬레이션 중 변경 불가
