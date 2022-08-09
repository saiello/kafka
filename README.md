# Kafka Collection for Ansible - saiello.kafka

## About

This Ansible Collection regroups several playbooks (packaged as role) to help install, setup and maintain Kafka (and its product counterpart [AMQ Streams on RHEL](https://access.redhat.com/documentation/en-us/red_hat_amq_streams/2.1/html-single/using_amq_streams_on_rhel) within the configuration management tool Ansible.

<!--start requires_ansible-->
## Ansible version compatibility

This collection has been tested against following Ansible versions: **>=2.9.10**.


## Install

Plugins and modules within a collection may be tested with only specific Ansible versions. A collection may contain metadata that identifies these versions.
<!--end requires_ansible-->

## Included content

### Roles

* [kafka_install](https://github.com/saiello/kafka/blob/main/roles/kafka_install/README.md): download and install
* [kafka_systemd_zookeeper](https://github.com/saiello/kafka/blob/main/roles/kafka_systemd_zookeeper/README.md): configure zookeeper systemd unit
* [kafka_systemd_broker](https://github.com/saiello/kafka/blob/main/roles/kafka_systemd_broker/README.md): configure kafka broker systemd unit


### Installing the collection

To install this Ansible collection:

    $ ansible-galaxy collection install saiello.kafka

or with a downloaded or built tarball, run the following command:

    $ ansible-galaxy collection install /path/to/saiello.kafka.tgz


## Building the collection

    $ ansible-galaxy collection build .


### Dependencies

- middleware_automation.redhat_csp_download
    - This collection is required to download resources from RedHat Customer Portal.
    - Documentation to collection can be found at <https://github.com/ansible-middleware/redhat-csp-download>


## License

[GNU General Public License v2.0](https://github.com/saiello/kafka/blob/main/LICENSE)