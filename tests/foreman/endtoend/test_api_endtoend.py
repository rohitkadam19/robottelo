# coding=utf-8
"""Smoke tests for the ``API`` end-to-end scenario.

@Requirement: Api endtoend

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: API

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""
import random

from fauxfactory import gen_string
from nailgun import client, entities
from robottelo import manifests
from robottelo.api.utils import (
    enable_rhrepo_and_fetchid,
    promote,
    upload_manifest,
)
from robottelo.config import settings
from robottelo.constants import (
    DEFAULT_LOC,
    DEFAULT_ORG,
    DEFAULT_SUBSCRIPTION_NAME,
    FAKE_0_PUPPET_REPO,
    CUSTOM_RPM_REPO,
    PRDS,
    REPOS,
    REPOSET,
)
from robottelo.decorators import (
    bz_bug_is_open,
    setting_is_set,
)
from robottelo.helpers import get_nailgun_config
from robottelo.test import TestCase
from six.moves import http_client
from .utils import AK_CONTENT_LABEL, ClientProvisioningMixin
# (too many public methods) pylint: disable=R0904

API_PATHS = {
    # flake8:noqa (line-too-long) pylint:disable=C0301
    u'activation_keys': (
        u'/katello/api/activation_keys',
        u'/katello/api/activation_keys',
        u'/katello/api/activation_keys/:id',
        u'/katello/api/activation_keys/:id',
        u'/katello/api/activation_keys/:id',
        u'/katello/api/activation_keys/:id/add_subscriptions',
        u'/katello/api/activation_keys/:id/content_override',
        u'/katello/api/activation_keys/:id/copy',
        u'/katello/api/activation_keys/:id/host_collections/available',
        u'/katello/api/activation_keys/:id/product_content',
        u'/katello/api/activation_keys/:id/releases',
        u'/katello/api/activation_keys/:id/remove_subscriptions',
    ),
    u'api': (),
    u'architectures': (
        u'/api/architectures',
        u'/api/architectures',
        u'/api/architectures/:id',
        u'/api/architectures/:id',
        u'/api/architectures/:id',
    ),
    u'audits': (
        u'/api/audits',
        u'/api/audits/:id',
    ),
    u'auth_source_ldaps': (
        u'/api/auth_source_ldaps',
        u'/api/auth_source_ldaps',
        u'/api/auth_source_ldaps/:id',
        u'/api/auth_source_ldaps/:id',
        u'/api/auth_source_ldaps/:id',
        u'/api/auth_source_ldaps/:id/test',
    ),
    u'autosign': (
        u'/api/smart_proxies/smart_proxy_id/autosign',
    ),
    u'base': (),
    u'bookmarks': (
        u'/api/bookmarks',
        u'/api/bookmarks',
        u'/api/bookmarks/:id',
        u'/api/bookmarks/:id',
        u'/api/bookmarks/:id',
    ),
    u'candlepin_proxies': (
        u'/katello/api/systems/:id/enabled_repos',
    ),
    u'capsule_content': (
        u'/katello/api/capsules/:id/content/available_lifecycle_environments',
        u'/katello/api/capsules/:id/content/lifecycle_environments',
        u'/katello/api/capsules/:id/content/lifecycle_environments',
        u'/katello/api/capsules/:id/content/lifecycle_environments/:environment_id',
        u'/katello/api/capsules/:id/content/sync',
        u'/katello/api/capsules/:id/content/sync',
        u'/katello/api/capsules/:id/content/sync',
    ),
    u'capsules': (
        u'/katello/api/capsules',
        u'/katello/api/capsules/:id',
    ),
    u'common_parameters': (
        u'/api/common_parameters',
        u'/api/common_parameters',
        u'/api/common_parameters/:id',
        u'/api/common_parameters/:id',
        u'/api/common_parameters/:id',
    ),
    u'compute_attributes': (
        u'/api/compute_resources/:compute_resource_id/compute_profiles/:compute_profile_id/compute_attributes',
        u'/api/compute_resources/:compute_resource_id/compute_profiles/:compute_profile_id/compute_attributes/:id',
    ),
    u'compute_profiles': (
        u'/api/compute_profiles',
        u'/api/compute_profiles',
        u'/api/compute_profiles/:id',
        u'/api/compute_profiles/:id',
        u'/api/compute_profiles/:id',
    ),
    u'compute_resources': (
        u'/api/compute_resources',
        u'/api/compute_resources',
        u'/api/compute_resources/:id',
        u'/api/compute_resources/:id',
        u'/api/compute_resources/:id',
        u'/api/compute_resources/:id/associate',
        u'/api/compute_resources/:id/available_clusters',
        u'/api/compute_resources/:id/available_clusters/:cluster_id/available_resource_pools',
        u'/api/compute_resources/:id/available_flavors',
        u'/api/compute_resources/:id/available_folders',
        u'/api/compute_resources/:id/available_images',
        u'/api/compute_resources/:id/available_networks',
        u'/api/compute_resources/:id/available_security_groups',
        u'/api/compute_resources/:id/available_storage_domains',
        u'/api/compute_resources/:id/available_storage_pods',
        u'/api/compute_resources/:id/available_zones',
    ),
    u'config_groups': (
        u'/api/config_groups',
        u'/api/config_groups',
        u'/api/config_groups/:id',
        u'/api/config_groups/:id',
        u'/api/config_groups/:id',
    ),
    u'config_reports': (
        u'/api/config_reports',
        u'/api/config_reports',
        u'/api/config_reports/:id',
        u'/api/config_reports/:id',
        u'/api/hosts/:host_id/config_reports/last',

    ),
    u'config_templates': (
        u'/api/config_templates',
        u'/api/config_templates',
        u'/api/config_templates/:id',
        u'/api/config_templates/:id',
        u'/api/config_templates/:id',
        u'/api/config_templates/:id/clone',
        u'/api/config_templates/build_pxe_default',
    ),
    u'content_uploads': (
        u'/katello/api/repositories/:repository_id/content_uploads',
        u'/katello/api/repositories/:repository_id/content_uploads/:id',
        u'/katello/api/repositories/:repository_id/content_uploads/:id',
    ),
    u'content_view_filter_rules': (
        u'/katello/api/content_view_filters/:content_view_filter_id/rules',
        u'/katello/api/content_view_filters/:content_view_filter_id/rules',
        u'/katello/api/content_view_filters/:content_view_filter_id/rules/:id',
        u'/katello/api/content_view_filters/:content_view_filter_id/rules/:id',
        u'/katello/api/content_view_filters/:content_view_filter_id/rules/:id',
    ),
    u'content_view_filters': (
        u'/katello/api/content_views/:content_view_id/filters',
        u'/katello/api/content_views/:content_view_id/filters',
        u'/katello/api/content_views/:content_view_id/filters/:id',
        u'/katello/api/content_views/:content_view_id/filters/:id',
        u'/katello/api/content_views/:content_view_id/filters/:id',
    ),
    u'content_view_puppet_modules': (
        u'/katello/api/content_views/:content_view_id/content_view_puppet_modules',
        u'/katello/api/content_views/:content_view_id/content_view_puppet_modules',
        u'/katello/api/content_views/:content_view_id/content_view_puppet_modules/:id',
        u'/katello/api/content_views/:content_view_id/content_view_puppet_modules/:id',
        u'/katello/api/content_views/:content_view_id/content_view_puppet_modules/:id',
    ),
    u'content_views': (
        u'/katello/api/content_views/:id',
        u'/katello/api/content_views/:id',
        u'/katello/api/content_views/:id',
        u'/katello/api/content_views/:id/available_puppet_module_names',
        u'/katello/api/content_views/:id/available_puppet_modules',
        u'/katello/api/content_views/:id/copy',
        u'/katello/api/content_views/:id/environments/:environment_id',
        u'/katello/api/content_views/:id/publish',
        u'/katello/api/content_views/:id/remove',
        u'/katello/api/organizations/:organization_id/content_views',
        u'/katello/api/organizations/:organization_id/content_views',
    ),
    u'containers': (
        u'/docker/api/v2/containers',
        u'/docker/api/v2/containers',
        u'/docker/api/v2/containers/:id',
        u'/docker/api/v2/containers/:id',
        u'/docker/api/v2/containers/:id/logs',
        u'/docker/api/v2/containers/:id/power',
    ),
    u'content_view_histories': (
        u'/katello/api/content_views/:id/history',
    ),
    u'content_view_versions': (
        u'/katello/api/content_view_versions',
        u'/katello/api/content_view_versions/:id',
        u'/katello/api/content_view_versions/:id',
        u'/katello/api/content_view_versions/:id/export',
        u'/katello/api/content_view_versions/:id/promote',
        u'/katello/api/content_view_versions/incremental_update',
    ),
    u'dashboard': (
        u'/api/dashboard',
    ),
    u'discovered_hosts': (
        u'/api/v2/discovered_hosts',
        u'/api/v2/discovered_hosts',
        u'/api/v2/discovered_hosts/:id',
        u'/api/v2/discovered_hosts/:id',
        u'/api/v2/discovered_hosts/:id',
        u'/api/v2/discovered_hosts/:id/auto_provision',
        u'/api/v2/discovered_hosts/:id/reboot',
        u'/api/v2/discovered_hosts/:id/refresh_facts',
        u'/api/v2/discovered_hosts/auto_provision_all',
        u'/api/v2/discovered_hosts/facts',
        u'/api/v2/discovered_hosts/reboot_all',
    ),
    u'discovery_rules': (
        u'/api/v2/discovery_rules',
        u'/api/v2/discovery_rules',
        u'/api/v2/discovery_rules/:id',
        u'/api/v2/discovery_rules/:id',
        u'/api/v2/discovery_rules/:id',
    ),
    u'disks': (
        u'/bootdisk/api',
        u'/bootdisk/api/generic',
        u'/bootdisk/api/hosts/:host_id',
    ),
    u'docker_manifests': (
        u'/katello/api/docker_manifests',
        u'/katello/api/docker_manifests/:id',
    ),
    u'docker_tags': (
        u'/katello/api/docker_tags',
        u'/katello/api/docker_tags/:id',
    ),
    u'domains': (
        u'/api/domains',
        u'/api/domains',
        u'/api/domains/:id',
        u'/api/domains/:id',
        u'/api/domains/:id',
    ),
    u'environments': (
        u'/api/environments',
        u'/api/environments',
        u'/api/environments/:id',
        u'/api/environments/:id',
        u'/api/environments/:id',
        u'/api/smart_proxies/:id/import_puppetclasses',
    ),
    u'errata': (
        u'/katello/api/errata',
        u'/katello/api/errata/:id',
        u'/katello/api/errata/compare',
    ),
    u'external_usergroups': (
        u'/api/usergroups/:usergroup_id/external_usergroups',
        u'/api/usergroups/:usergroup_id/external_usergroups',
        u'/api/usergroups/:usergroup_id/external_usergroups/:id',
        u'/api/usergroups/:usergroup_id/external_usergroups/:id',
        u'/api/usergroups/:usergroup_id/external_usergroups/:id',
        u'/api/usergroups/:usergroup_id/external_usergroups/:id/refresh',
    ),
    u'fact_values': (
        u'/api/fact_values',
    ),
    u'filters': (
        u'/api/filters',
        u'/api/filters',
        u'/api/filters/:id',
        u'/api/filters/:id',
        u'/api/filters/:id',
    ),
    u'foreign_input_sets': (
        '/api/templates/:template_id/foreign_input_sets',
        '/api/templates/:template_id/foreign_input_sets',
        '/api/templates/:template_id/foreign_input_sets/:id',
        '/api/templates/:template_id/foreign_input_sets/:id',
        '/api/templates/:template_id/foreign_input_sets/:id',
    ),
    u'foreman_openscap_arf_reports': (
        u'/api/v2/compliance/arf/:cname/:policy_id/:date',
        u'/api/v2/compliance/arf_reports',
        u'/api/v2/compliance/arf_reports/:id',
        u'/api/v2/compliance/arf_reports/:id',
    ),
    u'foreman_openscap_policies': (
        u'/api/v2/compliance/policies',
        u'/api/v2/compliance/policies',
        u'/api/v2/compliance/policies/:id',
        u'/api/v2/compliance/policies/:id',
        u'/api/v2/compliance/policies/:id',
        u'/api/v2/compliance/policies/:id/content',
    ),
    u'foreman_openscap_scap_contents': (
        u'/api/v2/compliance/scap_contents',
        u'/api/v2/compliance/scap_contents',
        u'/api/v2/compliance/scap_contents/:id',
        u'/api/v2/compliance/scap_contents/:id',
        u'/api/v2/compliance/scap_contents/:id',
    ),
    u'foreman_tasks': (
        u'/foreman_tasks/api/tasks',
        u'/foreman_tasks/api/tasks/:id',
        u'/foreman_tasks/api/tasks/bulk_resume',
        u'/foreman_tasks/api/tasks/bulk_search',
        u'/foreman_tasks/api/tasks/callback',
        u'/foreman_tasks/api/tasks/summary',
    ),
    u'gpg_keys': (
        u'/katello/api/gpg_keys',
        u'/katello/api/gpg_keys',
        u'/katello/api/gpg_keys/:id',
        u'/katello/api/gpg_keys/:id',
        u'/katello/api/gpg_keys/:id',
        u'/katello/api/gpg_keys/:id/content',
    ),
    u'home': (
        u'/api',
        u'/api/status',
    ),
    u'host_autocomplete': (),
    u'host_classes': (
        u'/api/hosts/:host_id/puppetclass_ids',
        u'/api/hosts/:host_id/puppetclass_ids',
        u'/api/hosts/:host_id/puppetclass_ids/:id',
    ),
    u'host_collections': (
        u'/katello/api/host_collections',
        u'/katello/api/host_collections',
        u'/katello/api/host_collections/:id',
        u'/katello/api/host_collections/:id',
        u'/katello/api/host_collections/:id',
        u'/katello/api/host_collections/:id/add_hosts',
        u'/katello/api/host_collections/:id/copy',
        u'/katello/api/host_collections/:id/remove_hosts',
    ),
    u'host_subscriptions': (
        '/api/hosts/:host_id/subscriptions',
        '/api/hosts/:host_id/subscriptions',
        '/api/hosts/:host_id/subscriptions/add_subscriptions',
        '/api/hosts/:host_id/subscriptions/auto_attach',
        '/api/hosts/:host_id/subscriptions/content_override',
        '/api/hosts/:host_id/subscriptions/events',
        '/api/hosts/:host_id/subscriptions/product_content',
        '/api/hosts/subscriptions',
    ),
    u'hostgroup_classes': (
        u'/api/hostgroups/:hostgroup_id/puppetclass_ids',
        u'/api/hostgroups/:hostgroup_id/puppetclass_ids',
        u'/api/hostgroups/:hostgroup_id/puppetclass_ids/:id',
    ),
    u'hostgroups': (
        u'/api/hostgroups',
        u'/api/hostgroups',
        u'/api/hostgroups/:id',
        u'/api/hostgroups/:id',
        u'/api/hostgroups/:id',
        u'/api/hostgroups/:id/clone',
    ),
    u'hosts': (
        u'/api/hosts',
        u'/api/hosts',
        u'/api/hosts/:host_id/host_collections',
        u'/api/hosts/:id',
        u'/api/hosts/:id',
        u'/api/hosts/:id',
        u'/api/hosts/:id/boot',
        u'/api/hosts/:id/disassociate',
        u'/api/hosts/:id/power',
        u'/api/hosts/:id/puppetrun',
        u'/api/hosts/:id/rebuild_config',
        u'/api/hosts/:id/status',
        u'/api/hosts/:id/status/:type',
        u'/api/hosts/:id/template/:kind',
        u'/api/hosts/:id/vm_compute_attributes',
        u'/api/hosts/facts',
    ),
    u'hosts_bulk_actions': (
        u'/katello/api/hosts/bulk/add_host_collections',
        u'/katello/api/hosts/bulk/applicable_errata',
        u'/katello/api/hosts/bulk/available_incremental_updates',
        u'/katello/api/hosts/bulk/destroy',
        u'/katello/api/hosts/bulk/environment_content_view',
        u'/katello/api/hosts/bulk/install_content',
        u'/katello/api/hosts/bulk/remove_content',
        u'/katello/api/hosts/bulk/remove_host_collections',
        u'/katello/api/hosts/bulk/update_content',
        u'/katello/api/hosts/bulk/subscriptions/add_subscriptions',
        u'/katello/api/hosts/bulk/subscriptions/auto_attach',
        u'/katello/api/hosts/bulk/subscriptions/remove_subscriptions',
    ),
    u'host_errata': (
        u'/api/hosts/:host_id/errata',
        u'/api/hosts/:host_id/errata/:id',
        u'/api/hosts/:host_id/errata/apply',
    ),
    u'host_packages': (
        u'/api/hosts/:host_id/packages',
        u'/api/hosts/:host_id/packages/install',
        u'/api/hosts/:host_id/packages/remove',
        u'/api/hosts/:host_id/packages/upgrade_all',
    ),
    u'images': (
        u'/api/compute_resources/:compute_resource_id/images',
        u'/api/compute_resources/:compute_resource_id/images',
        u'/api/compute_resources/:compute_resource_id/images/:id',
        u'/api/compute_resources/:compute_resource_id/images/:id',
        u'/api/compute_resources/:compute_resource_id/images/:id',
    ),
    u'interfaces': (
        u'/api/hosts/:host_id/interfaces',
        u'/api/hosts/:host_id/interfaces',
        u'/api/hosts/:host_id/interfaces/:id',
        u'/api/hosts/:host_id/interfaces/:id',
        u'/api/hosts/:host_id/interfaces/:id',
    ),
    u'job_invocations': (
        u'/api/job_invocations',
        u'/api/job_invocations',
        u'/api/job_invocations/:id',
        u'/api/job_invocations/:id/hosts/:host_id',
    ),
    u'job_templates': (
        u'/api/job_templates',
        u'/api/job_templates',
        u'/api/job_templates/:id',
        u'/api/job_templates/:id',
        u'/api/job_templates/:id',
        u'/api/job_templates/:id/clone',
        u'/api/job_templates/:id/export',
        u'/api/job_templates/import',
    ),
    u'lifecycle_environments': (
        u'/katello/api/environments',
        u'/katello/api/environments',
        u'/katello/api/environments/:id',
        u'/katello/api/environments/:id',
        u'/katello/api/environments/:id',
        u'/katello/api/organizations/:organization_id/environments/:id/repositories',
        u'/katello/api/organizations/:organization_id/environments/paths',
    ),
    u'locations': (
        u'/api/locations',
        u'/api/locations',
        u'/api/locations/:id',
        u'/api/locations/:id',
        u'/api/locations/:id',
    ),
    u'mail_notifications': (
        u'/api/mail_notifications',
        u'/api/mail_notifications/:id',
    ),
    u'media': (
        u'/api/media',
        u'/api/media',
        u'/api/media/:id',
        u'/api/media/:id',
        u'/api/media/:id',
    ),
    u'models': (
        u'/api/models',
        u'/api/models',
        u'/api/models/:id',
        u'/api/models/:id',
        u'/api/models/:id',
    ),
    u'operatingsystems': (
        u'/api/operatingsystems',
        u'/api/operatingsystems',
        u'/api/operatingsystems/:id',
        u'/api/operatingsystems/:id',
        u'/api/operatingsystems/:id',
        u'/api/operatingsystems/:id/bootfiles',
    ),
    u'organizations': (
        u'/katello/api/organizations',
        u'/katello/api/organizations',
        u'/katello/api/organizations/:id',
        u'/katello/api/organizations/:id',
        u'/katello/api/organizations/:id',
        u'/katello/api/organizations/:id/autoattach_subscriptions',
        u'/katello/api/organizations/:id/redhat_provider',
        u'/katello/api/organizations/:id/repo_discover',
        u'/katello/api/organizations/:label/cancel_repo_discover',
        u'/katello/api/organizations/:label/download_debug_certificate',
    ),
    u'os_default_templates': (
        u'/api/operatingsystems/:operatingsystem_id/os_default_templates',
        u'/api/operatingsystems/:operatingsystem_id/os_default_templates',
        u'/api/operatingsystems/:operatingsystem_id/os_default_templates/:id',
        u'/api/operatingsystems/:operatingsystem_id/os_default_templates/:id',
        u'/api/operatingsystems/:operatingsystem_id/os_default_templates/:id',
    ),
    u'ostree_branches': (
        u'/katello/api/compare',
        u'/katello/api/ostree_branches/:id',
    ),
    u'override_values': (
        u'/api/smart_variables/:smart_variable_id/override_values',
        u'/api/smart_variables/:smart_variable_id/override_values',
        u'/api/smart_variables/:smart_variable_id/override_values/:id',
        u'/api/smart_variables/:smart_variable_id/override_values/:id',
        u'/api/smart_variables/:smart_variable_id/override_values/:id',
    ),
    u'package_groups': (
        u'/katello/api/compare',
        u'/katello/api/package_groups/:id',
    ),
    u'packages': (
        u'/katello/api/compare',
        u'/katello/api/packages/:id',
    ),
    u'parameters': (
        u'/api/hosts/:host_id/parameters',
        u'/api/hosts/:host_id/parameters',
        u'/api/hosts/:host_id/parameters',
        u'/api/hosts/:host_id/parameters/:id',
        u'/api/hosts/:host_id/parameters/:id',
        u'/api/hosts/:host_id/parameters/:id',
    ),
    u'permissions': (
        u'/api/permissions',
        u'/api/permissions/:id',
        u'/api/permissions/resource_types',
    ),
    u'ping': (
        u'/katello/api/ping',
        u'/katello/api/status',
    ),
    u'plugins': (
        u'/api/plugins',
    ),
    u'products_bulk_actions': (
        u'/katello/api/products/bulk/destroy',
        u'/katello/api/products/bulk/sync_plan',
    ),
    u'products': (
        u'/katello/api/products',
        u'/katello/api/products',
        u'/katello/api/products/:id',
        u'/katello/api/products/:id',
        u'/katello/api/products/:id',
        u'/katello/api/products/:id/sync',
    ),
    u'provisioning_templates': (
        u'/api/provisioning_templates',
        u'/api/provisioning_templates',
        u'/api/provisioning_templates/:id',
        u'/api/provisioning_templates/:id',
        u'/api/provisioning_templates/:id',
        u'/api/provisioning_templates/:id/clone',
        u'/api/provisioning_templates/build_pxe_default',
    ),
    u'ptables': (
        u'/api/ptables',
        u'/api/ptables',
        u'/api/ptables/:id',
        u'/api/ptables/:id',
        u'/api/ptables/:id',
        u'/api/ptables/:id/clone',
    ),
    u'puppetclasses': (
        u'/api/puppetclasses',
        u'/api/puppetclasses',
        u'/api/puppetclasses/:id',
        u'/api/puppetclasses/:id',
        u'/api/puppetclasses/:id',
    ),
    u'puppet_modules': (
        u'/katello/api/compare',
        u'/katello/api/puppet_modules/:id',
    ),
    u'realms': (
        u'/api/realms',
        u'/api/realms',
        u'/api/realms/:id',
        u'/api/realms/:id',
        u'/api/realms/:id',
    ),
    u'recurring_logics': (
        u'/foreman_tasks/api/recurring_logics',
        u'/foreman_tasks/api/recurring_logics/:id',
        u'/foreman_tasks/api/recurring_logics/:id/cancel',
    ),
    u'registries': (
        u'/docker/api/v2/registries',
        u'/docker/api/v2/registries',
        u'/docker/api/v2/registries/:id',
        u'/docker/api/v2/registries/:id',
        u'/docker/api/v2/registries/:id',
    ),
    u'remote_execution_features': (
        '/api/remote_execution_features',
        '/api/remote_execution_features/:id',
        '/api/remote_execution_features/:id',
    ),
    u'reports': (
        u'/api/hosts/:host_id/reports/last',
        u'/api/reports',
        u'/api/reports',
        u'/api/reports/:id',
        u'/api/reports/:id',
    ),
    u'repositories_bulk_actions': (
        u'/katello/api/repositories/bulk/destroy',
        u'/katello/api/repositories/bulk/sync',
    ),
    u'repositories': (
        u'/katello/api/repositories',
        u'/katello/api/repositories',
        u'/katello/api/repositories/:id',
        u'/katello/api/repositories/:id',
        u'/katello/api/repositories/:id',
        u'/katello/api/repositories/:id/export',
        u'/katello/api/repositories/:id/gpg_key_content',
        u'/katello/api/repositories/:id/import_uploads',
        u'/katello/api/repositories/:id/sync',
        u'/katello/api/repositories/:id/upload_content',
        u'/katello/api/repositories/repository_types',
    ),
    u'repository_sets': (
        u'/katello/api/products/:product_id/repository_sets',
        u'/katello/api/products/:product_id/repository_sets/:id',
        u'/katello/api/products/:product_id/repository_sets/:id/available_repositories',
        u'/katello/api/products/:product_id/repository_sets/:id/disable',
        u'/katello/api/products/:product_id/repository_sets/:id/enable',
    ),
    u'roles': (
        u'/api/roles',
        u'/api/roles',
        u'/api/roles/:id',
        u'/api/roles/:id',
        u'/api/roles/:id',
    ),
    u'root': (),
    u'settings': (
        u'/api/settings',
        u'/api/settings/:id',
        u'/api/settings/:id',
    ),
    u'smart_class_parameters': (
        u'/api/smart_class_parameters',
        u'/api/smart_class_parameters/:id',
        u'/api/smart_class_parameters/:id',
    ),
    u'smart_proxies': (
        u'/api/smart_proxies',
        u'/api/smart_proxies',
        u'/api/smart_proxies/:id',
        u'/api/smart_proxies/:id',
        u'/api/smart_proxies/:id',
        u'/api/smart_proxies/:id/import_puppetclasses',
        u'/api/smart_proxies/:id/refresh',
    ),
    u'smart_variables': (
        u'/api/smart_variables',
        u'/api/smart_variables',
        u'/api/smart_variables/:id',
        u'/api/smart_variables/:id',
        u'/api/smart_variables/:id',
    ),
    u'statistics': (
        u'/api/statistics',
    ),
    u'subnet_disks': (
        u'/bootdisk/api',
        u'/bootdisk/api/subnets/:subnet_id',
    ),
    u'subnets': (
        u'/api/subnets',
        u'/api/subnets',
        u'/api/subnets/:id',
        u'/api/subnets/:id',
        u'/api/subnets/:id',
    ),
    u'subscriptions': (
        u'/katello/api/activation_keys/:activation_key_id/subscriptions',
        u'/katello/api/activation_keys/:activation_key_id/subscriptions/:id',
        u'/katello/api/organizations/:organization_id/subscriptions',
        u'/katello/api/organizations/:organization_id/subscriptions/delete_manifest',
        u'/katello/api/organizations/:organization_id/subscriptions/:id',
        u'/katello/api/organizations/:organization_id/subscriptions/manifest_history',
        u'/katello/api/organizations/:organization_id/subscriptions/refresh_manifest',
        u'/katello/api/organizations/:organization_id/subscriptions/upload',
    ),
    u'sync_plans': (
        u'/katello/api/organizations/:organization_id/sync_plans',
        u'/katello/api/organizations/:organization_id/sync_plans/:id',
        u'/katello/api/organizations/:organization_id/sync_plans/:id',
        u'/katello/api/organizations/:organization_id/sync_plans/:id',
        u'/katello/api/organizations/:organization_id/sync_plans/:id/add_products',
        u'/katello/api/organizations/:organization_id/sync_plans/:id/remove_products',
        u'/katello/api/sync_plans',
        u'/katello/api/sync_plans/:id/sync',
    ),
    u'sync': (
        u'/katello/api/organizations/:organization_id/products/:product_id/sync',
    ),
    u'systems': (
        u'/katello/api/systems',
        u'/katello/api/systems/:id',
        u'/katello/api/systems/:id',
        u'/katello/api/systems/:id/releases',
    ),
    u'tasks': (
        u'/api/orchestration/:id/tasks',
    ),
    u'template_combinations': (
        u'/api/config_templates/:config_template_id/template_combinations',
        u'/api/config_templates/:config_template_id/template_combinations',
        u'/api/provisioning_templates/:provisioning_template_id/template_combinations/:id',
        u'/api/template_combinations/:id',
        u'/api/template_combinations/:id',
    ),
    u'template_inputs': (
        '/api/templates/:template_id/template_inputs',
        '/api/templates/:template_id/template_inputs',
        '/api/templates/:template_id/template_inputs/:id',
        '/api/templates/:template_id/template_inputs/:id',
        '/api/templates/:template_id/template_inputs/:id',
    ),
    u'template_kinds': (
        u'/api/template_kinds',
    ),
    u'uebercerts': (
        u'/katello/api/organizations/:organization_id/uebercert',
    ),
    u'usergroups': (
        u'/api/usergroups',
        u'/api/usergroups',
        u'/api/usergroups/:id',
        u'/api/usergroups/:id',
        u'/api/usergroups/:id',
    ),
    u'users': (
        u'/api/users',
        u'/api/users',
        u'/api/users/:id',
        u'/api/users/:id',
        u'/api/users/:id',
    ),
}


class AvailableURLsTestCase(TestCase):
    """Tests for ``api/v2``."""
    longMessage = True
    maxDiff = None

    def setUp(self):
        """Define commonly-used variables."""
        self.path = '{0}/api/v2'.format(settings.server.get_url())

    def test_positive_get_status_code(self):
        """GET ``api/v2`` and examine the response.

        @id: 9d9c1afd-9158-419e-9a6e-91e9888f0c04

        @Assert: HTTP 200 is returned with an ``application/json`` content-type

        """
        response = client.get(
            self.path,
            auth=settings.server.get_credentials(),
            verify=False,
        )
        self.assertEqual(response.status_code, http_client.OK)
        self.assertIn('application/json', response.headers['content-type'])

    def test_positive_get_links(self):
        """GET ``api/v2`` and check the links returned.

        @id: 7b2dd77a-a821-485b-94db-b583f93c9a89

        @Assert: The paths returned are equal to ``API_PATHS``.

        """
        # Did the server give us any paths at all?
        response = client.get(
            self.path,
            auth=settings.server.get_credentials(),
            verify=False,
        )
        response.raise_for_status()
        # See below for an explanation of this transformation.
        api_paths = response.json()['links']
        for group, path_pairs in api_paths.items():
            api_paths[group] = list(path_pairs.values())

        if bz_bug_is_open(1166875):
            # The server returns incorrect paths.
            api_paths['docker_manifests'].append(u'/katello/api/docker_manifests')
            api_paths['docker_manifests'].remove(u'/katello/api/compare')
            api_paths['docker_tags'].append(u'/katello/api/docker_tags')
            api_paths['docker_tags'].remove(u'/katello/api/compare')
            api_paths['errata'].append(u'/katello/api/errata')
            api_paths['errata'].append(u'/katello/api/errata/compare')
            api_paths['errata'].remove(u'/katello/api/compare')

        self.assertEqual(
            frozenset(api_paths.keys()),
            frozenset(API_PATHS.keys())
        )
        for group in api_paths.keys():
            self.assertItemsEqual(api_paths[group], API_PATHS[group], group)

        # (line-too-long) pylint:disable=C0301
        # response.json()['links'] is a dict like this:
        #
        #     {u'content_views': {
        #          u'…': u'/katello/api/content_views/:id',
        #          u'…': u'/katello/api/content_views/:id/available_puppet_modules',
        #          u'…': u'/katello/api/organizations/:organization_id/content_views',
        #          u'…': u'/katello/api/organizations/:organization_id/content_views',
        #     }, …}
        #
        # We don't care about prose descriptions. It doesn't matter if those
        # change. Transform it before running any assertions:
        #
        #     {u'content_views': [
        #          u'/katello/api/content_views/:id',
        #          u'/katello/api/content_views/:id/available_puppet_modules',
        #          u'/katello/api/organizations/:organization_id/content_views',
        #          u'/katello/api/organizations/:organization_id/content_views',
        #     ], …}


class EndToEndTestCase(TestCase, ClientProvisioningMixin):
    """End-to-end tests using the ``API`` path."""

    @classmethod
    def setUpClass(cls):  # noqa
        super(EndToEndTestCase, cls).setUpClass()
        cls.fake_manifest_is_set = setting_is_set('fake_manifest')

    def test_positive_find_default_org(self):
        """Check if 'Default Organization' is present

        @id: c6e45b36-d8b6-4507-8dcd-0645668496b9

        @Assert: 'Default Organization' is found

        """
        results = entities.Organization().search(
            query={'search': 'name="{0}"'.format(DEFAULT_ORG)}
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, DEFAULT_ORG)

    def test_positive_find_default_loc(self):
        """Check if 'Default Location' is present

        @id: 1f40b3c6-488d-4037-a7ab-250a02bf919a

        @Assert: 'Default Location' is found

        """
        results = entities.Location().search(
            query={'search': 'name="{0}"'.format(DEFAULT_LOC)}
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, DEFAULT_LOC)

    def test_positive_find_admin_user(self):
        """Check if Admin User is present

        @id: 892fdfcd-18c0-42ef-988b-f13a04097f5c

        @Assert: Admin User is found and has Admin role

        """
        results = entities.User().search(query={'search': 'login=admin'})
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].login, 'admin')

    def test_positive_ping(self):
        """Check if all services are running

        @id: b8ecc7ba-8007-4067-bf99-21a82c833de7

        @Assert: Overall and individual services status should be 'ok'.

        """
        response = entities.Ping().search_json()
        self.assertEqual(response['status'], u'ok')  # overall status

        # Check that all services are OK. ['services'] is in this format:
        #
        # {u'services': {
        #    u'candlepin': {u'duration_ms': u'40', u'status': u'ok'},
        #    u'candlepin_auth': {u'duration_ms': u'41', u'status': u'ok'},
        #    …
        # }, u'status': u'ok'}
        services = response['services']
        if bz_bug_is_open('1325995'):
            services.pop('foreman_auth')
        self.assertTrue(
            all([service['status'] == u'ok' for service in services.values()]),
            u'Not all services seem to be up and running!'
        )

    def test_positive_end_to_end(self):
        """Perform end to end smoke tests using RH and custom repos.

        1. Create a new user with admin permissions
        2. Using the new user from above
            1. Create a new organization
            2. Clone and upload manifest
            3. Create a new lifecycle environment
            4. Create a custom product
            5. Create a custom YUM repository
            6. Create a custom PUPPET repository
            7. Enable a Red Hat repository
            8. Synchronize the three repositories
            9. Create a new content view
            10. Associate the YUM and Red Hat repositories to new content view
            11. Add a PUPPET module to new content view
            12. Publish content view
            13. Promote content view to the lifecycle environment
            14. Create a new activation key
            15. Add the products to the activation key
            16. Create a new libvirt compute resource
            17. Create a new subnet
            18. Create a new domain
            19. Create a new hostgroup and associate previous entities to it
            20. Provision a client

        @id: b2f73740-d3ce-4e6e-abc7-b23e5562bac1

        @Assert: All tests should succeed and Content should be successfully
        fetched by client.
        """
        # step 1: Create a new user with admin permissions
        login = gen_string('alphanumeric')
        password = gen_string('alphanumeric')
        entities.User(admin=True, login=login, password=password).create()

        # step 2.1: Create a new organization
        server_config = get_nailgun_config()
        server_config.auth = (login, password)
        org = entities.Organization(server_config).create()

        # step 2.2: Clone and upload manifest
        if self.fake_manifest_is_set:
            with manifests.clone() as manifest:
                upload_manifest(org.id, manifest.content)

        # step 2.3: Create a new lifecycle environment
        le1 = entities.LifecycleEnvironment(
            server_config,
            organization=org
        ).create()

        # step 2.4: Create a custom product
        prod = entities.Product(server_config, organization=org).create()
        repositories = []


        # step 2.5: Create custom YUM repository
        repo1 = entities.Repository(
            server_config,
            product=prod,
            content_type=u'yum',
            url=CUSTOM_RPM_REPO
        ).create()
        repositories.append(repo1)

        # step 2.6: Create custom PUPPET repository
        repo2 = entities.Repository(
            server_config,
            product=prod,
            content_type=u'puppet',
            url=FAKE_0_PUPPET_REPO
        ).create()
        repositories.append(repo2)

        # step 2.7: Enable a Red Hat repository
        if self.fake_manifest_is_set:
            repo3 = entities.Repository(id=enable_rhrepo_and_fetchid(
                basearch='x86_64',
                org_id=org.id,
                product=PRDS['rhel'],
                repo=REPOS['rhva6']['name'],
                reposet=REPOSET['rhva6'],
                releasever='6Server',
            ))
            repositories.append(repo3)

        # step 2.8: Synchronize the three repositories
        for repo in repositories:
            repo.sync()

        # step 2.9: Create content view
        content_view = entities.ContentView(
            server_config,
            organization=org
        ).create()

        # step 2.10: Associate the YUM and Red Hat repositories to new content
        # view
        repositories.remove(repo2)
        content_view.repository = repositories
        content_view = content_view.update(['repository'])


        # step 2.11: Add a PUPPET module to new content view
        puppet_mods = content_view.available_puppet_modules()
        self.assertGreater(len(puppet_mods['results']), 0)
        puppet_module = random.choice(puppet_mods['results'])
        puppet = entities.ContentViewPuppetModule(
            author=puppet_module['author'],
            content_view=content_view,
            name=puppet_module['name'],
        ).create()
        self.assertEqual(
            puppet.name,
            puppet_module['name'],
        )

        # step 2.12: Publish content view
        content_view.publish()

        # step 2.13: Promote content view to the lifecycle environment
        content_view = content_view.read()
        self.assertEqual(len(content_view.version), 1)
        cv_version = content_view.version[0].read()
        self.assertEqual(len(cv_version.environment), 1)
        promote(cv_version, le1.id)
        # check that content view exists in lifecycle
        content_view = content_view.read()
        self.assertEqual(len(content_view.version), 1)
        cv_version = cv_version.read()

        # step 2.14: Create a new activation key
        activation_key_name = gen_string('alpha')
        activation_key = entities.ActivationKey(
            name=activation_key_name,
            environment=le1,
            organization=org,
            content_view=content_view,
        ).create()

        # step 2.15: Add the products to the activation key
        for sub in entities.Subscription(organization=org).search():
            if sub.read_json()['product_name'] == DEFAULT_SUBSCRIPTION_NAME:
                activation_key.add_subscriptions(data={
                    'quantity': 1,
                    'subscription_id': sub.id,
                })
                break
        # step 2.15.1: Enable product content
        if self.fake_manifest_is_set:
            activation_key.content_override(data={'content_override': {
                u'content_label': AK_CONTENT_LABEL,
                u'value': u'1',
            }})

        # BONUS: Create a content host and associate it with promoted
        # content view and last lifecycle where it exists
        content_host = entities.Host(
            content_facet_attributes={
                'content_view_id': content_view.id,
                'lifecycle_environment_id': le1.id,
            },
            organization=org,
        ).create()
        # check that content view matches what we passed
        self.assertEqual(
            content_host.content_facet_attributes['content_view_id'],
            content_view.id
        )
        # check that lifecycle environment matches
        self.assertEqual(
            content_host.content_facet_attributes['lifecycle_environment_id'],
            le1.id
        )

        # step 2.16: Create a new libvirt compute resource
        entities.LibvirtComputeResource(
            server_config,
            url=u'qemu+ssh://root@{0}/system'.format(
                settings.compute_resources.libvirt_hostname
            ),
        ).create()

        # step 2.17: Create a new subnet
        subnet = entities.Subnet(server_config).create()

        # step 2.18: Create a new domain
        domain = entities.Domain(server_config).create()

        # step 2.19: Create a new hostgroup and associate previous entities to
        # it
        entities.HostGroup(
            server_config,
            domain=domain,
            subnet=subnet
        ).create()

        # step 2.20: Provision a client
        self.client_provisioning(activation_key_name, org.label)
