# Interview follow-up drill

Answers refer to the actual implementation, not hypothetical deployed capabilities.

1. What if timestamps go backward? ingest rejects relative to both source order and tick watermark; tick rejects regression.
2. What if the calibration reference is wrong? Estimates can be consistently misaligned; the implementation does not infer truth from content. Supply trusted probes and quantify their uncertainty next.
3. Why not wait for the slowest sensor? That makes one missing source block the timeline. A caller watermark and maximum age give explicit degradation.
4. Can a future sample influence an old tick? The buffer selection requires sample time at or before tick time. The no-future-leakage test covers it.
5. Can a stream exhaust memory? Stream count and per-stream capacity are capped; overflow evicts oldest and increments a counter.
6. Can history exhaust disk? Yes. There is no retention daemon yet. Run duration is bounded, but accumulated history needs a retention/backup policy.
7. Is a repeated held sample independent information? No. The scalar model can become overconfident. Model temporal correlation or update only on new measurements before claiming calibrated confidence intervals.
8. Why does dropout not stop output? The random-walk prediction continues without measurements and uncertainty increases.
9. What breaks if you add API workers? Each worker could own independent active-run/session state. This deployment explicitly supports one process only.
10. Could SQLite acknowledge an uncommitted frame? Runtime.produce awaits Store.append's transaction context before broadcasting.
11. What if a worker dies during the transaction? The child-process crash test leaves only the committed batch; startup marks the run interrupted.
12. What if two viewers have different speeds? Each has its own bounded queue and skipped count, separate from durable history.
13. Does the queue bound all socket memory? No. Transport buffers also exist; viewer count and send timeout cap exposure but do not provide a precise total-memory bound.
14. Why not Kafka? The implemented scale and single-owner state do not justify distributed log complexity; adopting it would still need per-run ordering and state checkpoint semantics.
15. How would you verify an offset estimator? Inject known drift, jitter, missed probes and discontinuities; evaluate alignment error independently of fused signal RMSE.
16. What does a successful hash comparison establish? Equal canonical output bytes on replay for this build. It is not proof of physical model correctness.
17. What if someone forges a cookie? Session identifiers are random and server-validated. CSRF additionally binds mutation/socket proof to that session.
18. Why does free hosting threaten persistence? The provided free-tier config has ephemeral disk. It cannot claim durable history across instance replacement.
19. What does the dependency failure demonstrate? The saved pre-fix npm scan caught the vulnerable build dependency, and the patched lockfile was rescanned. It does not prove the entire app is vulnerability-free.
20. What is the next most valuable experiment? A known-clock public or hardware stream with realistic jitter and independent ground truth, followed by a sustained browser-arrival latency and dropout campaign.
