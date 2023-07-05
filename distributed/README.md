# Worker Topics
* blockchain/worker/chain
* blockchain/worker/mine
* blockchain/worker/add
* blockchain/worker/times
* blockchain/worker/worker_id/read
* blockchain/worker/config

# API Topics
* blockchain/api/block_winner
* blockchain/api/notification

# Topic reset
```bash
mosquitto_pub -h localhost -t test -u admin -P password -n -r -d
```
