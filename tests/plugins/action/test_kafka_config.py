import pytest
import yaml

from plugins.action.kafka_config import KafkaConfigGenerator, ActionModule


@pytest.fixture
def yaml_args():
    return yaml.safe_load("""
advertised_host: localhost

authorization:
  type: simple
  deny_by_default: true
  super_users:
  - CN:admin

tls:
  enabled: true
  trustedCA:
    file: ../../../molecule/shared/certs/ca-root.pem
    location: /etc/certs/ca-root.pem
  keystore:
    file: ../../../molecule/shared/certs/cert-cluster.p12
    location: /etc/certs/cert-cluster.p12
    password: changeit
    type: PKCS12

listeners:
- name: replication
  port: 9091
  tls: true 
  authentication:
    type: tls

- name: authenticated
  port: 9094
  tls: true 
  authentication:
    type: scram-sha-512

- name: admin
  port: 9095
  tls: true 
  authentication:
    type: tls

additional_config:
  num.partitions: 1

admin:
  listener_name: admin
  authentication:
    type: tls
  tls:
    enabled: true
    trustedCA:
      file: ../../../molecule/shared/certs/ca-root.pem
      location: /etc/certs/ca-root.pem
    keystore:
      file: ../../../molecule/shared/certs/cert-admin.p12
      location: /etc/certs/cert-admin.p12
      password: changeit
      type: PKCS12
""")

def test_convert_empty_configuration():
    actual = KafkaConfigGenerator({}).get_kafka_config()
    assert actual['core']['listeners'] == 'PLAINTEXT://:9092'
    assert actual['core']['advertised.listeners'] == 'PLAINTEXT://localhost:9092'
    assert actual['core']['listener.security.protocol.map'] == 'PLAINTEXT:PLAINTEXT'
    assert actual['authorization'] == {}

def test_convert_kafka_config(yaml_args):
    actual = KafkaConfigGenerator(yaml_args).get_kafka_config()
    assert actual['core']['listeners'] == 'replication://:9091,authenticated://:9094,admin://:9095'
    assert actual['core']['advertised.listeners'] == 'replication://localhost:9091,authenticated://localhost:9094,admin://localhost:9095'
    assert actual['core']['listener.security.protocol.map'] == 'replication:SSL,authenticated:SASL_SSL,admin:SSL'
    assert actual['authorization']['authorizer.class.name'] == 'kafka.security.authorizer.AclAuthorizer'
    assert actual['listeners']['authenticated']['sasl']['scram-sha-512'] == 'org.apache.kafka.common.security.scram.ScramLoginModule required;'

def test_convert_admin_configuration(yaml_args):
    kafka_config_generator = KafkaConfigGenerator(yaml_args)
    kafka_config = kafka_config_generator.get_kafka_config()
    actual = kafka_config_generator.get_admin_config(kafka_config)
    assert actual['listener'] == 'localhost:9095'
    assert actual['options']['ssl.truststore.location'] == '/etc/certs/ca-root.pem'
    assert actual['options']['ssl.truststore.type'] == 'PEM'
    assert actual['options']['ssl.keystore.location'] == '/etc/certs/cert-admin.p12'
    assert actual['options']['ssl.keystore.type'] == 'PKCS12'
    assert actual['options']['ssl.keystore.password'] == 'changeit'
    
  