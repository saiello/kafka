import pytest
import yaml

from plugins.action.kafka_config import KafkaConfigGenerator, ActionModule


@pytest.fixture
def base_yaml_config():
    return yaml.safe_load("""
advertised_host: localhost

authorization:
  type: simple
  deny_by_default: true
  super_users:
  - CN:admin

tls:
  enabled: true
  trustedCA: defaultCA.pem
  keystore:
    location: cert.p12
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

""")

def test_convert_empty_configuration():
  # given
    kcc = KafkaConfigGenerator({})

    # when
    actual = kcc.kafka_config
    
    # then
    assert actual['core']['listeners'] == 'PLAINTEXT://:9092'
    assert actual['core']['advertised.listeners'] == 'PLAINTEXT://localhost:9092'
    assert actual['core']['listener.security.protocol.map'] == 'PLAINTEXT:PLAINTEXT'
    assert actual['authorization'] == {}

def test_convert_kafka_config(base_yaml_config):
    # given
    kcc = KafkaConfigGenerator(base_yaml_config)

    # when
    actual = kcc.kafka_config
    
    # then
    assert actual['core']['listeners'] == 'REPLICATION://:9091,AUTHENTICATED://:9094,ADMIN://:9095'
    assert actual['core']['advertised.listeners'] == 'REPLICATION://localhost:9091,AUTHENTICATED://localhost:9094,ADMIN://localhost:9095'
    assert actual['core']['listener.security.protocol.map'] == 'REPLICATION:SSL,AUTHENTICATED:SASL_SSL,ADMIN:SSL'
    assert actual['authorization']['authorizer.class.name'] == 'kafka.security.authorizer.AclAuthorizer'
    assert actual['listeners']['authenticated']['sasl']['scram-sha-512'] == 'org.apache.kafka.common.security.scram.ScramLoginModule required;'


def test_convert_admin_configuration_auth_tls(base_yaml_config):

    # given
    yaml_override = yaml.safe_load("""
admin:
  listener_name: admin
  tls:
    trustedCA: /ect/certs/ca-root.pem
    keystore:
      location: /etc/certs/cert-admin.p12
      password: changeit
      type: PKCS12   
  authentication: 
    type: tls
""")

    yaml_config = base_yaml_config | yaml_override
    kafka_config_generator = KafkaConfigGenerator(yaml_config)
  
    # when
    actual = kafka_config_generator.admin_config
    
    # then
    assert actual['listener'] == 'localhost:9095'
    assert actual['options']['ssl.truststore.location'] == '/ect/certs/ca-root.pem'
    assert actual['options']['ssl.truststore.type'] == 'PEM'
    assert actual['options']['ssl.keystore.location'] == '/etc/certs/cert-admin.p12'
    assert actual['options']['ssl.keystore.type'] == 'PKCS12'
    assert actual['options']['ssl.keystore.password'] == 'changeit'
