# Performance Problems

Why is it so slow?

**Last Updated:** February 8, 2026
**Audience:** Performance Engineers

> **Before Reading This**
>
> You should understand:
> - [Performance Monitoring](../09_operations/performance_monitoring.md)
> - [Profiling Tools](../06_developer_guides/performance_tuning.md)

## High CPU

*Symptom:* Dashboard is unresponsive.
*Cause:* Vector re-indexing or heavy regex parsing.
*Diagnosis:* Use `py-spy`.

## High Memory

*Symptom:* OOM Kill (Exit Code 137).
*Cause:* Loading huge files into RAM.
*Fix:* Stream file reads. Increase container memory limit.

## Slow API Responses

*Symptom:* TTFB (Time To First Byte) > 1s.
*Cause:* Synchronous blocking DB calls in async path.
*Fix:* Ensure `await db.execute()` is used.

## Related Reading

- [Performance Tuning](../06_developer_guides/performance_tuning.md)
- [Scaling Guide](../08_deployment/scaling_guide.md)
