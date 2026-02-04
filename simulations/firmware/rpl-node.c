#include "contiki.h"
#include "net/routing/routing.h"
#include "net/netstack.h"
#include "net/ipv6/simple-udp.h"
#include "net/ipv6/uipbuf.h"
#include "net/ipv6/uip.h"
#include "net/ipv6/uip-udp-packet.h"
#include "net/ipv6/uip-ds6.h"
#include "net/routing/rpl-classic/rpl.h"
#include "random.h"
#include "net/linkaddr.h"

#include <stdio.h>
#include <string.h>

#ifndef ATTACKER_ID
#define ATTACKER_ID 6
#endif
#ifndef ATTACK_RATE
#define ATTACK_RATE 0.0
#endif
#ifndef ROOT_ID
#define ROOT_ID 1
#endif
#ifndef SEND_INTERVAL
#define SEND_INTERVAL 30
#endif
#ifndef SEND_JITTER
#define SEND_JITTER 5
#endif
#ifndef DATA_PORT
#define DATA_PORT 3000
#endif
#ifndef ATTACK_STATS_PERIOD
#define ATTACK_STATS_PERIOD 300
#endif

typedef struct {
  uint32_t seq;
  uint32_t send_time_ms;
  uint16_t src_id;
} __attribute__((packed)) data_packet_t;

static struct simple_udp_connection udp_conn;
static uint32_t seq_id = 0;
static uint32_t attacker_recv = 0;
static uint32_t attacker_fwd = 0;
static uint32_t attacker_drop = 0;
static uint16_t last_parent_id = 0;
static uint32_t parent_churn = 0;

static uint32_t
now_ms(void)
{
  return (uint32_t)((clock_time() * 1000UL) / CLOCK_SECOND);
}

static uint16_t
lladdr_to_node_id(const linkaddr_t *lladdr)
{
  if(lladdr == NULL) {
    return 0;
  }
  return (uint16_t)lladdr->u8[LINKADDR_SIZE - 1];
}

static void
log_parent_change(void)
{
  rpl_dag_t *dag = rpl_get_any_dag();
  if(dag == NULL || dag->preferred_parent == NULL) {
    return;
  }
  const linkaddr_t *lladdr = rpl_get_parent_lladdr(dag->preferred_parent);
  uint16_t parent_id = lladdr_to_node_id(lladdr);
  if(parent_id == 0) {
    return;
  }
  if(last_parent_id != 0 && last_parent_id != parent_id) {
    parent_churn++;
  }
  if(last_parent_id != parent_id) {
    printf("OBS ts=%lu node=%u ev=PARENT parent=%u rank=%u\n",
           (unsigned long)now_ms(),
           (unsigned)linkaddr_node_addr.u8[LINKADDR_SIZE - 1],
           (unsigned)parent_id,
           (unsigned)dag->rank);
    last_parent_id = parent_id;
  }
}

static enum netstack_ip_action
ip_input(void)
{
  uint8_t proto = 0;
  uipbuf_get_last_header(uip_buf, uip_len, &proto);
  if(proto == UIP_PROTO_UDP && linkaddr_node_addr.u8[LINKADDR_SIZE - 1] == ATTACKER_ID) {
    uint16_t dest_port = UIP_UDP_BUF->destport;
    if(dest_port == UIP_HTONS(DATA_PORT)) {
      attacker_recv++;
      printf("OBS ts=%lu node=%u ev=DATA_RX\n",
             (unsigned long)now_ms(),
             (unsigned)ATTACKER_ID);
    }
  }
  return NETSTACK_IP_PROCESS;
}

static enum netstack_ip_action
ip_output(const linkaddr_t *localdest)
{
  uint8_t proto = 0;
  uipbuf_get_last_header(uip_buf, uip_len, &proto);
  if(proto == UIP_PROTO_UDP && linkaddr_node_addr.u8[LINKADDR_SIZE - 1] == ATTACKER_ID) {
    uint8_t is_me = uip_ds6_is_my_addr(&UIP_IP_BUF->srcipaddr);
    uint16_t dest_port = UIP_UDP_BUF->destport;
    if(!is_me && dest_port == UIP_HTONS(DATA_PORT)) {
      uint16_t drop_rand = random_rand() % 1000;
      uint16_t threshold = (uint16_t)(ATTACK_RATE * 1000.0);
      if(drop_rand < threshold) {
        attacker_drop++;
        printf("OBS ts=%lu node=%u ev=DATA_DROP reason=attack\n",
               (unsigned long)now_ms(),
               (unsigned)ATTACKER_ID);
        return NETSTACK_IP_DROP;
      }
      attacker_fwd++;
      printf("OBS ts=%lu node=%u ev=DATA_FWD\n",
             (unsigned long)now_ms(),
             (unsigned)ATTACKER_ID);
    }
  }
  return NETSTACK_IP_PROCESS;
}

static struct netstack_ip_packet_processor packet_processor = {
  .process_input = ip_input,
  .process_output = ip_output
};

static void
udp_rx_callback(struct simple_udp_connection *c,
                const uip_ipaddr_t *sender_addr,
                uint16_t sender_port,
                const uip_ipaddr_t *receiver_addr,
                uint16_t receiver_port,
                const uint8_t *data,
                uint16_t datalen)
{
  if(linkaddr_node_addr.u8[LINKADDR_SIZE - 1] != ROOT_ID) {
    return;
  }
  if(datalen < sizeof(data_packet_t)) {
    return;
  }
  data_packet_t packet;
  memcpy(&packet, data, sizeof(packet));
  uint32_t delay = now_ms() - packet.send_time_ms;
  printf("OBS ts=%lu node=%u ev=ROOT_RX seq=%lu src=%u\n",
         (unsigned long)now_ms(),
         (unsigned)ROOT_ID,
         (unsigned long)packet.seq,
         (unsigned)packet.src_id);
  printf("OBS ts=%lu node=%u ev=DELAY seq=%lu src=%u delay_ms=%lu\n",
         (unsigned long)now_ms(),
         (unsigned)ROOT_ID,
         (unsigned long)packet.seq,
         (unsigned)packet.src_id,
         (unsigned long)delay);
}

PROCESS(rpl_node_process, "RPL Node");
AUTOSTART_PROCESSES(&rpl_node_process);

PROCESS_THREAD(rpl_node_process, ev, data)
{
  static struct etimer send_timer;
  static struct etimer parent_timer;
  static struct etimer attack_timer;
  static uip_ipaddr_t root_ipaddr;

  PROCESS_BEGIN();

  if(linkaddr_node_addr.u8[LINKADDR_SIZE - 1] == ROOT_ID) {
    NETSTACK_ROUTING.root_start();
    printf("OBS ts=%lu node=%u ev=ROOT\n",
           (unsigned long)now_ms(),
           (unsigned)ROOT_ID);
  }

  simple_udp_register(&udp_conn, DATA_PORT, NULL, DATA_PORT, udp_rx_callback);

  if(linkaddr_node_addr.u8[LINKADDR_SIZE - 1] == ATTACKER_ID) {
    netstack_ip_packet_processor_add(&packet_processor);
    printf("OBS ts=%lu node=%u ev=ATTACK_START rate=%.2f\n",
           (unsigned long)now_ms(),
           (unsigned)ATTACKER_ID,
           (double)ATTACK_RATE);
  }

  etimer_set(&send_timer, CLOCK_SECOND * SEND_INTERVAL);
  etimer_set(&parent_timer, CLOCK_SECOND * 10);
  etimer_set(&attack_timer, CLOCK_SECOND * ATTACK_STATS_PERIOD);

  while(1) {
    PROCESS_WAIT_EVENT();

    if(etimer_expired(&parent_timer)) {
      if(NETSTACK_ROUTING.node_has_joined()) {
        log_parent_change();
      }
      etimer_reset(&parent_timer);
    }

    if(etimer_expired(&send_timer)) {
      if(linkaddr_node_addr.u8[LINKADDR_SIZE - 1] != ROOT_ID &&
         NETSTACK_ROUTING.node_has_joined() &&
         NETSTACK_ROUTING.get_root_ipaddr(&root_ipaddr)) {
        data_packet_t packet;
        packet.seq = ++seq_id;
        packet.send_time_ms = now_ms();
        packet.src_id = linkaddr_node_addr.u8[LINKADDR_SIZE - 1];

        simple_udp_sendto(&udp_conn, &packet, sizeof(packet), &root_ipaddr);
        printf("OBS ts=%lu node=%u ev=DATA_TX seq=%lu dst=%u\n",
               (unsigned long)now_ms(),
               (unsigned)packet.src_id,
               (unsigned long)packet.seq,
               (unsigned)ROOT_ID);
      }
      etimer_set(&send_timer, CLOCK_SECOND * (SEND_INTERVAL + (random_rand() % (SEND_JITTER + 1))));
    }

    if(etimer_expired(&attack_timer)) {
      if(linkaddr_node_addr.u8[LINKADDR_SIZE - 1] == ATTACKER_ID) {
        printf("OBS ts=%lu node=%u ev=ATTACK_STATS recv=%lu fwd=%lu drop=%lu\n",
               (unsigned long)now_ms(),
               (unsigned)ATTACKER_ID,
               (unsigned long)attacker_recv,
               (unsigned long)attacker_fwd,
               (unsigned long)attacker_drop);
      }
      etimer_reset(&attack_timer);
    }
  }

  PROCESS_END();
}
