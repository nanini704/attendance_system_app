import redis

# Connect to Redis Client
hostname = 'redis-16313.c15.us-east-1-2.ec2.redns.redis-cloud.com'
portnumber = '16313'
password = 'wHVGowA6401qo6CSQc3bpXZyAhAFNlP2'

r = redis.StrictRedis(host=hostname,
                      port=portnumber,
                      password=password)

# Simulated Logs
with open('simulated_logs.txt', 'r') as f:
    logs_text = f.read()

encoded_logs = logs_text.split('\n')

# Push into Redis database
r.lpush('attendance:logss', *encoded_logs)
