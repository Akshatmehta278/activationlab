output "application_url" {
  value       = "http://${aws_lb.main.dns_name}"
  description = "Reference deployment URL. Add ACM/HTTPS before real internet-facing production use."
}

output "mysql_endpoint" {
  value       = aws_db_instance.mysql.address
  description = "RDS endpoint."
}

output "redis_endpoint" {
  value       = aws_elasticache_replication_group.redis.primary_endpoint_address
  description = "Redis primary endpoint."
}

output "rabbitmq_endpoints" {
  value       = aws_mq_broker.rabbit.instances[0].endpoints
  description = "RabbitMQ broker endpoints."
  sensitive   = true
}
