from ansible.plugins.action import ActionBase
from ansible.module_utils.common.arg_spec import ArgumentSpecValidator


DEFAULT_LISTENERS = [{
  'name': 'PLAINTEXT',
  'port': 9092,
  'protocol': 'PLAINTEXT'
}]

tls_config_spec = dict(
  type='dict',
  options=dict(
    enabled=dict(
      type='bool'
    ),
    keystore=dict(
      type='dict',
      options=dict(
        file=dict(type='str'),
        location=dict(type='str'),
        password=dict(type='str'),
        type=dict(type='str')
      )
    ),
    trustedCA=dict(
      type='dict',
      options=dict(
        file=dict(type='str'),
        location=dict(type='str')
      )
    )
  )
)

authentication_spec = dict(
  type='dict',
  options=dict(
    type=dict(
      type='str',
      choices=['none', 'plain', 'tls', 'scram-sha-256', 'scram-sha-512', 'oauthbearer', 'gssapi']
    ),
    config=dict(
      type='dict'
    )
  )
)

argument_config_spec = dict(
  advertised_host=dict(
    type='str'
  ),
  tls=tls_config_spec,
  authorization=dict(
    type='dict',
    options=dict(
      type=dict(
        type='str'
      ),
      deny_by_default=dict(
        type='bool',
        default=True
      ),
      super_users=dict(
        type='str'
      )
    )
  ),
  listeners=dict(
    type='list',
    elements='dict',
    options=dict(
      name=dict(
        type='str'
      ),
      port=dict(
        type='int'
      ),
      tls=dict(
        type='bool'
      ),
      authentication=authentication_spec
    )
  ),
  additional_config=dict(
    type='dict'
  ),
  admin=dict(
    type='dict',
    options=dict(
      listener_name=dict(
        type='str'
      ),
      tls=tls_config_spec,
      authentication=authentication_spec
    )
  )
)


argument_spec_data = dict(
    config=argument_config_spec
)

class ActionModule(ActionBase):


  def run(self, tmp=None, task_vars=None):

    config = self._task.args.pop('config', {})

    generator = KafkaConfigGenerator(config)
    kafka_config = generator.get_kafka_config()

    ret = dict()
    ret['__kafka_config'] = kafka_config
    ret['__admin_config'] = generator.get_admin_config(kafka_config)
    

    return dict(ansible_facts=dict(ret))


class KafkaConfigGenerator():

  def __init__(self, config):
    self._config = config

    validator = ArgumentSpecValidator(argument_config_spec)
    validation_result = validator.validate(config)

    if validation_result.error_messages:
      raise ValueError(validation_result.error_messages)



  def _coalesce_listeners(self, listeners):

    advertised_host = self._config.pop('advertised_host', 'localhost')
    tls = self._config.pop('tls', {})
    listener_map = dict()

    for listener in listeners:
    
      if 'advertised' not in listener:
        listener['advertised'] = advertised_host

      is_tls = 'tls' in listener and listener['tls']
      sasl = 'authentication' in listener and listener['authentication']['type'] not in ['tls', 'none']

      if sasl and is_tls:
        listener['protocol'] = 'SASL_SSL'
      elif sasl:
        listener['protocol'] = 'SASL_PLAINTEXT'
      elif is_tls:
        listener['protocol'] = 'SSL'
      else:
        listener['protocol'] = 'PLAINTEXT'

      if tls:
        listener['truststore_type'] = 'PEM'
        listener['truststore_location'] = tls['trustedCA']['location']
        
        listener['keystore_location'] = tls['keystore']['location']
        listener['keystore_password'] = tls['keystore']['password']
        listener['keystore_type']  = tls['keystore']['type']
       
      if 'authentication' in listener:
        authentication = listener['authentication']
        authentication_type = authentication['type']
        authentication_config = authentication.pop('config', {})
        
        jaas_login_module_args = ' \\\\n'.join(['{}="{}"'.rjust(9, ' ')
          .format(k, v) for k, v in authentication_config.items()])

        if authentication_type == 'tls':
          listener['ssl_client_auth'] = authentication_config.pop('tls_client_auth', 'required')

        if authentication_type in ['scram-sha-256', 'scram-sha-512']:
          listener['sasl'] = {
            authentication_type: authentication_config.pop('jaas_config', 'org.apache.kafka.common.security.scram.ScramLoginModule required;')
          }
        
        if authentication_type in ['oauthbearer']:
          listener['sasl'] = {
            authentication_type: authentication_config.pop('jaas_config', 'org.apache.kafka.common.security.oauthbearer.OAuthBearerLoginModule required \\\\n{};'
              .format(jaas_login_module_args))
          }

        if authentication_type in ['gssapi']:
          listener['sasl'] = {
            authentication_type: authentication_config.pop('jaas_config', 'com.sun.security.auth.module.Krb5LoginModule required \\\\n{};'
              .format(jaas_login_module_args))
          }

        if authentication_type == 'plain':
          pass # TODO 
      
      listener_map[listener['name']] = listener

    return listener_map

  def _authorization_config(self):
    """Build the authorization config dictionary"""

    if 'authorization' not in self._config or not self._config['authorization']:
      return {}
    
    authorization = self._config['authorization']
    deny_by_default = authorization.pop('deny_by_default', True)
    
    return {
      'authorizer.class.name': 'kafka.security.authorizer.AclAuthorizer', # TODO use proper class according to kafka version
      'allow.everyone.if.no.acl.found': 'false' if deny_by_default else 'true',
      'super.users': authorization.pop('super_users') # TODO set a default value if available
    }

  def get_kafka_config(self):
      listeners = self._config.pop('listeners', DEFAULT_LISTENERS)
      listeners = self._coalesce_listeners(listeners)
      
      config = dict()
      config['listeners'] = listeners
      config['authorization'] = self._authorization_config()
      config['additional_config'] = self._config.pop('additional_config', {})

      listeners = listeners.values()
      
      config['core'] = {
        'advertised.listeners': ','.join(['{name}://{advertised}:{port}'.format(**listener) for listener in listeners]),
        'listeners': ','.join(['{name}://:{port}'.format(**listener) for listener in listeners]),
        'listener.security.protocol.map': ','.join(['{name}:{protocol}'.format(**listener) for listener in listeners]),
      }

      return config

  def get_admin_config(self, kafka_config):
    admin = self._config.pop('admin')
    if admin is None:
      return {}

    allowed_listeners = kafka_config['listeners'].keys()
    listener_name = admin.pop('listener_name')
    if listener_name not in allowed_listeners:
      raise ValueError("Admin listener_name '%s' is invalid. Allowed values are: %s " % (listener_name, allowed_listeners))

    listener = kafka_config['listeners'][listener_name]
    protocol = listener['protocol']
  
    options = {}
    
    authentication = admin.pop('authentication', {})
    tls = authentication.pop('tls', {})
    
    if 'trustedCA' in tls:
      options['ssl.truststore.location']=tls['trustedCA']['location']
      options['ssl.truststore.type']='PEM'
   
    if 'keystore' in tls:
      options['ssl.keystore.location']=tls['keystore']['location']
      options['ssl.keystore.type']=tls['keystore']['type']
      options['ssl.keystore.password']=tls['keystore']['password']

    authentication_type = authentication.pop('type', '-')
    authentication_config = authentication.pop('config', {})

    

    if authentication_type == 'plain':
      jaas_login_module_args = ' '.join(['{}="{}"'.rjust(9, ' ')
        .format(k, v) for k, v in authentication_config.items()])
      options['sasl.jaas.config']='org.apache.kafka.common.security.plain.PlainLoginModule required {};'.format(jaas_login_module_args)

    if authentication_type == 'gssapi':

      options['sasl.mechanism'] = 'GSSAPI'
      options['sasl.kerberos.service.name'] = authentication_config.pop('service_name', 'kafka')

      jaas_login_module_args = ' '.join(['{}="{}"'.rjust(9, ' ')
        .format(k, v) for k, v in authentication_config.items()])

      options['sasl.jaas.config']='com.sun.security.auth.module.Krb5LoginModule required {};'.format(jaas_login_module_args)

    if authentication_type in ['scram-sha-256', 'scram-sha-512']:
      options['sasl.mechanism'] = authentication_type.upper()
      jaas_login_module_args = ' '.join(['{}="{}"'.rjust(9, ' ')
        .format(k, v) for k, v in authentication_config.items()])
      options['sasl.jaas.config']='org.apache.kafka.common.security.scram.ScramLoginModule required {};'.format(jaas_login_module_args)
    
    # TODO check options according to protocol 

    return {
      'host': listener['advertised'],
      'port': listener['port'],
      'protocol': protocol,
      'listener': '%s:%s' % (listener['advertised'], listener['port']),
      'require_command_config': bool(options),
      'options': options 
    }
