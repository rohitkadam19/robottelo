# -*- encoding: utf-8 -*-
"""Test class for Repository UI

@Requirement: Repository

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: UI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""

import time

from fauxfactory import gen_string
from nailgun import entities
from robottelo import ssh
from robottelo.constants import (
    CHECKSUM_TYPE,
    DOCKER_REGISTRY_HUB,
    FAKE_0_PUPPET_REPO,
    FAKE_1_YUM_REPO,
    FAKE_2_YUM_REPO,
    FAKE_YUM_DRPM_REPO,
    FAKE_YUM_SRPM_REPO,
    FEDORA22_OSTREE_REPO,
    FEDORA23_OSTREE_REPO,
    REPO_DISCOVERY_URL,
    REPO_TYPE,
    VALID_GPG_KEY_BETA_FILE,
    VALID_GPG_KEY_FILE,
    DOWNLOAD_POLICIES
)
from robottelo.datafactory import (
    filtered_datapoint,
    generate_strings_list,
    invalid_values_list,
)
from robottelo.decorators import run_only_on, stubbed, tier1, tier2
from robottelo.decorators.host import skip_if_os
from robottelo.helpers import read_data_file
from robottelo.test import UITestCase
from robottelo.ui.factory import make_contentview, make_repository, set_context
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.session import Session
from selenium.common.exceptions import NoSuchElementException


@filtered_datapoint
def valid_repo_names_docker_sync():
    """Returns a list of valid repo names for docker sync test"""
    return [
        gen_string('alpha', 8).lower(),
        gen_string('numeric', 8),
        gen_string('alphanumeric', 8).lower(),
        gen_string('html', 8),
        gen_string('utf8', 8),
    ]


class RepositoryTestCase(UITestCase):
    """Implements Repos tests in UI"""

    @classmethod
    def setUpClass(cls):
        super(RepositoryTestCase, cls).setUpClass()
        # create instances to be shared across the sessions
        cls.session_loc = entities.Location().create()
        cls.session_prod = entities.Product(
            organization=cls.session_org).create()

    @classmethod
    def set_session_org(cls):
        """Creates new organization to be used for current session the
        session_user will login automatically with this org in context
        """
        cls.session_org = entities.Organization().create()

    def setup_navigate_syncnow(self, session, prd_name, repo_name):
        """Helps with Navigation for syncing via the repos page."""
        strategy1, value1 = locators['repo.select']
        strategy2, value2 = locators['repo.select_checkbox']
        session.nav.go_to_select_org(self.session_org.name, force=False)
        session.nav.go_to_products()
        session.nav.click((strategy1, value1 % prd_name))
        session.nav.click((strategy2, value2 % repo_name))
        session.nav.click(locators['repo.sync_now'])

    def prd_sync_is_ok(self, repo_name):
        """Asserts whether the sync Result is successful."""
        strategy1, value1 = locators['repo.select_event']
        self.repository.click(tab_locators['prd.tab_tasks'])
        self.repository.click((strategy1, value1 % repo_name))
        timeout = time.time() + 60 * 10
        spinner = self.repository.wait_until_element(
            locators['repo.result_spinner'], 20)
        # Waits until result spinner is visible on the UI or times out
        # after 10mins
        while spinner:
            if time.time() > timeout:
                break
            spinner = self.repository.wait_until_element(
                locators['repo.result_spinner'], 3)
        result = self.repository.wait_until_element(
            locators['repo.result_event']).text
        return result == 'success'

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_name(self):
        """Create repository with different names and minimal input
        parameters

        @id: 3713c811-ea80-43ce-a753-344d1dcb7486

        @Assert: Repository is created successfully
        """
        prod = entities.Product(organization=self.session_org).create()
        with Session(self.browser) as session:
            for repo_name in generate_strings_list():
                with self.subTest(repo_name):
                    set_context(session, org=self.session_org.name)
                    self.products.search(prod.name).click()
                    make_repository(
                        session,
                        name=repo_name,
                        url=FAKE_1_YUM_REPO,
                    )
                    self.assertIsNotNone(self.repository.search(repo_name))

    @run_only_on('sat')
    @tier2
    def test_positive_create_in_different_orgs(self):
        """Create repository in two different orgs with same name

        @id: 019c2242-8802-4bae-82c5-accf8f793dbc

        @Assert: Repository is created successfully for both organizations

        @CaseLevel: Integration
        """
        org_2 = entities.Organization(name=gen_string('alpha')).create()
        product_1 = entities.Product(organization=self.session_org).create()
        product_2 = entities.Product(organization=org_2).create()
        with Session(self.browser) as session:
            for repo_name in generate_strings_list():
                with self.subTest(repo_name):
                    set_context(session, org=self.session_org.name)
                    self.products.search(product_1.name).click()
                    make_repository(
                        session,
                        name=repo_name,
                        url=FAKE_1_YUM_REPO,
                    )
                    self.assertIsNotNone(self.repository.search(repo_name))
                    set_context(session, org=org_2.name)
                    self.products.search(product_2.name).click()
                    make_repository(
                        session,
                        name=repo_name,
                        url=FAKE_1_YUM_REPO,
                        force_context=True,
                    )
                    self.assertIsNotNone(self.repository.search(repo_name))

    @run_only_on('sat')
    @tier1
    def test_positive_create_repo_with_checksum(self):
        """Create repository with checksum type as sha256.

        @id: 06f37bb3-b0cf-4f1f-ae12-df13a6a7eaab

        @Assert: Repository is created with expected checksum type.
        """
        checksum = CHECKSUM_TYPE[u'sha256']
        # Creates new product
        product = entities.Product(organization=self.session_org).create()
        with Session(self.browser) as session:
            for repo_name in generate_strings_list():
                with self.subTest(repo_name):
                    set_context(session, org=self.session_org.name)
                    self.products.search(product.name).click()
                    make_repository(
                        session,
                        name=repo_name,
                        url=FAKE_1_YUM_REPO,
                        repo_checksum=checksum,
                    )
                    self.assertTrue(self.repository.validate_field(
                        repo_name, 'checksum', checksum))

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_invalid_name(self):
        """Create repository with invalid names

        @id: 385d0222-6466-4bc0-9686-b215f41e4274

        @Assert: Repository is not created
        """
        # Creates new product
        product = entities.Product(organization=self.session_org).create()
        for repo_name in invalid_values_list(interface='ui'):
            with self.subTest(repo_name):
                with Session(self.browser) as session:
                    set_context(session, org=self.session_org.name)
                    self.products.search(product.name).click()
                    make_repository(
                        session,
                        name=repo_name,
                        url=FAKE_1_YUM_REPO,
                    )
                    invalid = self.products.wait_until_element(
                        common_locators['common_invalid'])
                    self.assertIsNotNone(invalid)

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_same_names(self):
        """Try to create two repositories with same name

        @id: f9515a61-0c5e-4767-9fc9-b17d440418d8

        @Assert: Repository is not created
        """
        repo_name = gen_string('alphanumeric')
        product = entities.Product(organization=self.session_org).create()
        with Session(self.browser) as session:
            set_context(session, org=self.session_org.name)
            self.products.search(product.name).click()
            make_repository(
                session,
                name=repo_name,
                url=FAKE_1_YUM_REPO,
            )
            self.assertIsNotNone(self.repository.search(repo_name))
            self.products.search(product.name).click()
            make_repository(
                session,
                name=repo_name,
                url=FAKE_1_YUM_REPO,
            )
            self.assertTrue(self.products.wait_until_element(
                common_locators['common_invalid']))

    @run_only_on('sat')
    @tier1
    def test_positive_update_url(self):
        """Update content repository with new URL

        @id: cb864338-9d18-4e18-a2ee-37f22e7036b8

        @Assert: Repository is updated with expected url value
        """
        product = entities.Product(organization=self.session_org).create()
        with Session(self.browser) as session:
            for repo_name in generate_strings_list():
                with self.subTest(repo_name):
                    set_context(session, org=self.session_org.name)
                    self.products.search(product.name).click()
                    make_repository(
                        session,
                        name=repo_name,
                        url=FAKE_1_YUM_REPO,
                    )
                    self.assertIsNotNone(self.repository.search(repo_name))
                    self.assertTrue(self.repository.validate_field(
                        repo_name, 'url', FAKE_1_YUM_REPO))
                    self.products.search(product.name).click()
                    self.repository.update(repo_name, new_url=FAKE_2_YUM_REPO)
                    self.products.search(product.name).click()
                    self.assertTrue(self.repository.validate_field(
                        repo_name, 'url', FAKE_2_YUM_REPO))

    @run_only_on('sat')
    @tier1
    def test_positive_update_gpg(self):
        """Update content repository with new gpg-key

        @id: 51da6572-02d0-43d7-96cc-895b5bebfadb

        @Assert: Repository is updated with new gpg key
        """
        repo_name = gen_string('alphanumeric')
        key_1_content = read_data_file(VALID_GPG_KEY_FILE)
        key_2_content = read_data_file(VALID_GPG_KEY_BETA_FILE)
        # Create two new GPGKey's
        gpgkey_1 = entities.GPGKey(
            content=key_1_content,
            organization=self.session_org,
        ).create()
        gpgkey_2 = entities.GPGKey(
            content=key_2_content,
            organization=self.session_org,
        ).create()
        product = entities.Product(organization=self.session_org).create()
        with Session(self.browser) as session:
            set_context(session, org=self.session_org.name)
            self.products.search(product.name).click()
            make_repository(
                session,
                name=repo_name,
                url=FAKE_1_YUM_REPO,
                gpg_key=gpgkey_1.name,
            )
            self.assertIsNotNone(self.repository.search(repo_name))
            self.assertTrue(self.repository.validate_field(
                repo_name, 'gpgkey', gpgkey_1.name))
            self.products.search(product.name).click()
            self.repository.update(repo_name, new_gpg_key=gpgkey_2.name)
            self.products.search(product.name).click()
            self.assertTrue(self.repository.validate_field(
                repo_name, 'gpgkey', gpgkey_2.name))

    @run_only_on('sat')
    @tier1
    def test_positive_update_checksum_type(self):
        """Update content repository with new checksum type

        @id: eed4e77d-baa2-42c2-9774-f1bed52efe39

        @Assert: Repository is updated with expected checksum type.
        """
        repo_name = gen_string('alphanumeric')
        checksum_default = CHECKSUM_TYPE['default']
        checksum_update = CHECKSUM_TYPE['sha1']
        product = entities.Product(organization=self.session_org).create()
        with Session(self.browser) as session:
            set_context(session, org=self.session_org.name)
            self.products.search(product.name).click()
            make_repository(
                session,
                name=repo_name,
                url=FAKE_1_YUM_REPO,
            )
            self.assertIsNotNone(self.repository.search(repo_name))
            self.assertTrue(self.repository.validate_field(
                repo_name, 'checksum', checksum_default))
            self.products.search(product.name).click()
            self.repository.update(
                repo_name, new_repo_checksum=checksum_update)
            self.products.search(product.name).click()
            self.assertTrue(self.repository.validate_field(
                repo_name, 'checksum', checksum_update))

    @run_only_on('sat')
    @tier1
    def test_positive_delete(self):
        """Create content repository and then remove it

        @id: 9edc93b1-d4e5-453e-b4ee-0731df491397

        @Assert: Repository is deleted successfully
        """
        product = entities.Product(organization=self.session_org).create()
        with Session(self.browser) as session:
            for repo_name in generate_strings_list():
                with self.subTest(repo_name):
                    set_context(session, org=self.session_org.name)
                    self.products.search(product.name).click()
                    make_repository(
                        session,
                        name=repo_name,
                        url=FAKE_1_YUM_REPO,
                    )
                    self.assertIsNotNone(self.repository.search(repo_name))
                    self.repository.delete(repo_name)

    @run_only_on('sat')
    @stubbed
    @tier2
    def test_negative_delete_puppet_repo_associated_with_cv(self):
        """Delete a puppet repo associated with a content view - BZ#1271000

        @id: 72639e14-4089-4f40-bad7-e18021ad376f

        @Steps:

        1. Create a new product
        2. Create a new puppet repo, no sync source
        3. Upload a puppet module (say ntpd) to repo
        4. Create a CV, go to add puppet modules page
        5. Add latest version of the puppet module from Step 3
        6. View puppet repo details, it should show "Latest (Currently X.Y.Z)"
        7. Go back to product, drill down into repo and delete the puppet
        module from Step 3
        8. Go back to same CV puppet module details page

        @Assert: Proper error message saying that the puppet module version is
        not found

        @caseautomation: notautomated

        @CaseLevel: Integration
        """

    @run_only_on('sat')
    @tier2
    def test_positive_discover_repo_via_existing_product(self):
        """Create repository via repo-discovery under existing product

        @id: 9181950c-a756-456f-a46a-059e7a2add3c

        @Assert: Repository is discovered and created

        @CaseLevel: Integration
        """
        discovered_urls = 'fakerepo01/'
        product = entities.Product(organization=self.session_org).create()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.session_org.name, force=False)
            session.nav.go_to_products()
            self.repository.discover_repo(
                url_to_discover=REPO_DISCOVERY_URL,
                discovered_urls=[discovered_urls],
                product=product.name,
            )

    @run_only_on('sat')
    @tier2
    def test_positive_discover_repo_via_new_product(self):
        """Create repository via repo discovery under new product

        @id: dc5281f8-1a8a-4a17-b746-728f344a1504

        @Assert: Repository is discovered and created

        @CaseLevel: Integration
        """
        product_name = gen_string('alpha')
        discovered_urls = 'fakerepo01/'
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.session_org.name)
            session.nav.go_to_select_loc(self.session_loc.name)
            session.nav.go_to_products()
            self.repository.discover_repo(
                url_to_discover=REPO_DISCOVERY_URL,
                discovered_urls=[discovered_urls],
                product=product_name,
                new_product=True,
            )
            self.assertIsNotNone(self.products.search(product_name))

    @run_only_on('sat')
    @tier2
    def test_positive_sync_custom_repo_yum(self):
        """Create Custom yum repos and sync it via the repos page.

        @id: afa218f4-e97a-4240-a82a-e69538d837a1

        @Assert: Sync procedure for specific yum repository is successful

        @CaseLevel: Integration
        """
        product = entities.Product(organization=self.session_org).create()
        with Session(self.browser) as session:
            for repo_name in generate_strings_list():
                with self.subTest(repo_name):
                    # Creates new yum repository using api
                    entities.Repository(
                        name=repo_name,
                        url=FAKE_1_YUM_REPO,
                        product=product,
                    ).create()
                    self.setup_navigate_syncnow(
                        session,
                        product.name,
                        repo_name,
                    )
                    # prd_sync_is_ok returns boolean values and not objects
                    self.assertTrue(self.prd_sync_is_ok(repo_name))

    @run_only_on('sat')
    @tier2
    def test_positive_sync_custom_repo_puppet(self):
        """Create Custom puppet repos and sync it via the repos page.

        @id: 135176cc-7664-41ee-8c41-b77e193f2f22

        @Assert: Sync procedure for specific puppet repository is successful

        @CaseLevel: Integration
        """
        # Creates new product
        product = entities.Product(organization=self.session_org).create()
        with Session(self.browser) as session:
            for repo_name in generate_strings_list():
                with self.subTest(repo_name):
                    # Creates new puppet repository
                    entities.Repository(
                        name=repo_name,
                        url=FAKE_0_PUPPET_REPO,
                        product=product,
                        content_type=REPO_TYPE['puppet'],
                    ).create()
                    self.setup_navigate_syncnow(
                        session,
                        product.name,
                        repo_name,
                    )
                    # prd_sync_is_ok returns boolean values and not objects
                    self.assertTrue(self.prd_sync_is_ok(repo_name))

    @run_only_on('sat')
    @tier2
    def test_positive_sync_custom_repo_docker(self):
        """Create Custom docker repos and sync it via the repos page.

        @id: 942e0b4f-3524-4f00-812d-bdad306f81de

        @Assert: Sync procedure for specific docker repository is successful

        @CaseLevel: Integration
        """
        # Creates new product
        product = entities.Product(organization=self.session_org).create()
        with Session(self.browser) as session:
            for repo_name in valid_repo_names_docker_sync():
                with self.subTest(repo_name):
                    # Creates new docker repository
                    entities.Repository(
                        name=repo_name,
                        url=DOCKER_REGISTRY_HUB,
                        product=product,
                        content_type=REPO_TYPE['docker'],
                    ).create()
                    self.setup_navigate_syncnow(
                        session, product.name, repo_name
                    )
                    # prd_sync_is_ok returns boolean values and not objects
                    self.assertTrue(self.prd_sync_is_ok(repo_name))

    @run_only_on('sat')
    @skip_if_os('RHEL6')
    @tier1
    def test_positive_create_custom_ostree_repo(self):
        """Create Custom ostree repository.

        @id: 852cccdc-7289-4d2f-b23a-7caad2dfa195

        @Assert: Create custom ostree repository should be successful
        """
        prod = entities.Product(organization=self.session_org).create()
        with Session(self.browser) as session:
            for repo_name in generate_strings_list():
                with self.subTest(repo_name):
                    session.nav.go_to_select_org(
                        self.session_org.name, force=False)
                    self.products.click(self.products.search(prod.name))
                    make_repository(
                        session,
                        name=repo_name,
                        repo_type=REPO_TYPE['ostree'],
                        url=FEDORA23_OSTREE_REPO,
                    )
                    self.assertIsNotNone(self.repository.search(repo_name))

    @run_only_on('sat')
    @skip_if_os('RHEL6')
    @tier1
    def test_positive_delete_custom_ostree_repo(self):
        """Delete custom ostree repository.

        @id: 87dcb236-4eb4-4897-9c2a-be1d0f4bc3e7

        @Assert: Delete custom ostree repository should be successful
        """
        prod = entities.Product(organization=self.session_org).create()
        repo_name = gen_string('alphanumeric')
        # Creates new ostree repository using api
        entities.Repository(
            name=repo_name,
            content_type='ostree',
            url=FEDORA22_OSTREE_REPO,
            product=prod,
            unprotected=False,
        ).create()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.session_org.name, force=False)
            self.products.click(self.products.search(prod.name))
            self.assertIsNotNone(self.repository.search(repo_name))
            self.repository.delete(repo_name)

    @run_only_on('sat')
    @skip_if_os('RHEL6')
    @tier1
    def test_positive_update_custom_ostree_repo_name(self):
        """Update custom ostree repository name.

        @id: 098ee88f-6cdb-45e0-850a-e1b71662f7ab

        @Steps: Update repo name

        @Assert: ostree repo name should be updated successfully
        """
        prod = entities.Product(organization=self.session_org).create()
        repo_name = gen_string('alphanumeric')
        new_repo_name = gen_string('numeric')
        # Creates new ostree repository using api
        entities.Repository(
            name=repo_name,
            content_type='ostree',
            url=FEDORA22_OSTREE_REPO,
            product=prod,
            unprotected=False,
        ).create()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.session_org.name, force=False)
            self.products.click(self.products.search(prod.name))
            self.assertIsNotNone(self.repository.search(repo_name))
            self.repository.update(
                repo_name, new_name=new_repo_name)
            self.products.click(self.products.search(prod.name))
            self.assertIsNotNone(self.repository.search(new_repo_name))

    @run_only_on('sat')
    @skip_if_os('RHEL6')
    @tier1
    def test_positive_update_custom_ostree_repo_url(self):
        """Update custom ostree repository url.

        @id: dfd392f9-6f1d-4d87-a43b-ced40606b8c2

        @Steps: Update ostree repo URL

        @Assert: ostree repo URL should be updated successfully
        """
        prod = entities.Product(organization=self.session_org).create()
        repo_name = gen_string('alphanumeric')
        # Creates new ostree repository using api
        entities.Repository(
            name=repo_name,
            content_type='ostree',
            url=FEDORA22_OSTREE_REPO,
            product=prod,
            unprotected=False,
        ).create()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.session_org.name, force=False)
            self.products.click(self.products.search(prod.name))
            self.assertIsNotNone(self.repository.search(repo_name))
            self.repository.update(
                repo_name,
                new_url=FEDORA23_OSTREE_REPO
            )
            self.products.click(self.products.search(prod.name))
            # Validate the new repo URL
            self.assertTrue(
                self.repository.validate_field(
                    repo_name, 'url', FEDORA23_OSTREE_REPO
                )
            )

    @tier1
    def test_positive_download_policy_displayed_for_yum_repos(self):
        """Verify that YUM repositories can be created with download policy

        @id: 8037a68b-66b8-4b42-a80b-fb08495f948d

        @Assert: Dropdown for download policy is displayed for yum repo
        """
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.session_org.name, force=False)
            self.products.search_and_click(self.session_prod.name)
            self.repository.navigate_to_entity()
            self.repository.click(locators['repo.new'])
            self.repository.assign_value(
                common_locators['name'], gen_string('alphanumeric'))
            self.repository.assign_value(locators['repo.type'], 'yum')
            self.assertIsNotNone(
                self.repository.find_element(locators['repo.download_policy'])
            )

    @tier1
    def test_positive_create_with_download_policy(self):
        """Create YUM repositories with available download policies

        @id: 8099fb98-963d-4370-bf51-6807f5efd6d3

        @Assert: YUM repository with a download policy is created
        """
        repo_name = gen_string('alpha')
        with Session(self.browser) as session:
            for policy in DOWNLOAD_POLICIES.values():
                with self.subTest(policy):
                    self.products.search_and_click(self.session_prod.name)
                    make_repository(
                        session,
                        name=repo_name,
                        repo_type=REPO_TYPE['yum'],
                        download_policy=policy
                    )
                    self.assertIsNotNone(self.repository.search(repo_name))

    @tier1
    def test_positive_create_with_default_download_policy(self):
        """Verify if the default download policy is assigned when creating
        a YUM repo without `download_policy` field

        @id: ee7637fe-3864-4b2f-a153-14312658d75a

        @Assert: YUM repository with a default download policy
        """
        repo_name = gen_string('alphanumeric')
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.session_org.name, force=False)
            self.products.search_and_click(self.session_prod.name)
            make_repository(session, name=repo_name, repo_type='yum')
            self.assertTrue(
                self.repository.validate_field(
                    repo_name, 'download_policy', 'Immediate'
                )
            )

    def _create_yum_repo_with_download_policy(self, name, download_policy):
        """Helper method to create a new yum repository using API"""
        return entities.Repository(
            name=name,
            content_type='yum',
            product=self.session_prod,
            download_policy=download_policy.lower().replace(' ', '_')
        ).create()

    # All *_update_to_* tests below could be grouped in to a single test_case
    # using a loop But for clarity we decided to keep as separated tests

    @tier1
    def test_positive_create_immediate_update_to_on_demand(self):
        """Update `immediate` download policy to `on_demand` for a newly
        created YUM repository

        @id: 4aa4d914-74f3-4c2e-9e8a-6e1b7fdb34ea

        @Assert: immediate download policy is updated to on_demand
        """
        repo_name = gen_string('alphanumeric')
        self._create_yum_repo_with_download_policy(repo_name, 'Immediate')
        with Session(self.browser):
            self.products.search_and_click(self.session_prod.name)
            self.repository.update(repo_name, download_policy='On Demand')
            self.assertTrue(
                self.repository.validate_field(
                    repo_name, 'download_policy', 'On Demand'
                )
            )

    @tier1
    def test_positive_create_immediate_update_to_background(self):
        """Update `immediate` download policy to `background` for a newly
        created YUM repository

        @id: d61bf6b6-6485-4d3a-816a-b533e96deb69

        @Assert: immediate download policy is updated to background
        """
        repo_name = gen_string('alphanumeric')
        self._create_yum_repo_with_download_policy(repo_name, 'Immediate')
        with Session(self.browser):
            self.products.search_and_click(self.session_prod.name)
            self.repository.update(repo_name, download_policy='Background')
            self.assertTrue(
                self.repository.validate_field(
                    repo_name, 'download_policy', 'Background'
                )
            )

    @tier1
    def test_positive_create_on_demand_update_to_immediate(self):
        """Update `on_demand` download policy to `immediate` for a newly
        created YUM repository

        @id: 51cac66d-05a4-47da-adb5-d2909725457e

        @Assert: on_demand download policy is updated to immediate
        """
        repo_name = gen_string('alphanumeric')
        self._create_yum_repo_with_download_policy(repo_name, 'On Demand')
        with Session(self.browser):
            self.products.search_and_click(self.session_prod.name)
            self.repository.update(repo_name, download_policy='Immediate')
            self.assertTrue(
                self.repository.validate_field(
                    repo_name, 'download_policy', 'Immediate'
                )
            )

    @tier1
    def test_positive_create_on_demand_update_to_background(self):
        """Update `on_demand` download policy to `background` for a newly
        created YUM repository

        @id: 25b5ba4e-a1cf-41c2-8ca8-4fa3153570f8

        @Assert: on_demand download policy is updated to background
        """
        repo_name = gen_string('alphanumeric')
        self._create_yum_repo_with_download_policy(repo_name, 'On Demand')
        with Session(self.browser):
            self.products.search_and_click(self.session_prod.name)
            self.repository.update(repo_name, download_policy='Background')
            self.assertTrue(
                self.repository.validate_field(
                    repo_name, 'download_policy', 'Background'
                )
            )

    @tier1
    def test_positive_create_background_update_to_immediate(self):
        """Update `background` download policy to `immediate` for a newly
        created YUM repository

        @id: 7a6efe70-8edb-4fa8-b2a4-93762d6e4bc5

        @Assert: background download policy is updated to immediate
        """
        repo_name = gen_string('alphanumeric')
        self._create_yum_repo_with_download_policy(repo_name, 'Background')
        with Session(self.browser):
            self.products.search_and_click(self.session_prod.name)
            self.repository.update(repo_name, download_policy='Immediate')
            self.assertTrue(
                self.repository.validate_field(
                    repo_name, 'download_policy', 'Immediate'
                )
            )

    @tier1
    def test_positive_create_background_update_to_on_demand(self):
        """Update `background` download policy to `on_demand` for a newly
        created YUM repository

        @id: d36b96b1-6e09-455e-82e7-36a23f8c6c06

        @Assert: background download policy is updated to on_demand
        """
        repo_name = gen_string('alphanumeric')
        self._create_yum_repo_with_download_policy(repo_name, 'Background')
        with Session(self.browser):
            self.products.search_and_click(self.session_prod.name)
            self.repository.update(repo_name, download_policy='On Demand')
            self.assertTrue(
                self.repository.validate_field(
                    repo_name, 'download_policy', 'On Demand'
                )
            )

    @tier1
    def test_negative_create_with_invalid_download_policy(self):
        """Verify that YUM repository cannot be created with invalid download
        policy

        @id: dded6dda-3576-4485-8f3c-bb7c091e7ff2

        @Assert: YUM repository is not created with invalid download policy
        """
        repo_name = gen_string('alphanumeric')
        with Session(self.browser) as session:
            self.products.search_and_click(self.session_prod.name)
            invalid = gen_string('alpha', 5)
            msg = "Could not locate element with visible text: %s" % invalid
            with self.assertRaisesRegexp(NoSuchElementException, msg):
                make_repository(
                    session,
                    name=repo_name,
                    repo_type='yum',
                    download_policy=invalid
                )

    @tier1
    def test_negative_update_to_invalid_download_policy(self):
        """Verify that YUM repository cannot be updated to invalid download
        policy

        @id: e6c725f2-172e-49f6-ae92-c56af8a1200b

        @Assert: YUM repository is not updated to invalid download policy
        """
        repo_name = gen_string('alphanumeric')
        self._create_yum_repo_with_download_policy(repo_name, 'Immediate')
        with Session(self.browser):
            self.products.search_and_click(self.session_prod.name)
            invalid = gen_string('alpha', 5)
            msg = "Could not locate element with visible text: %s" % invalid
            with self.assertRaisesRegexp(NoSuchElementException, msg):
                self.repository.update(
                    repo_name,
                    download_policy=invalid
                )

    @tier1
    def test_negative_download_policy_displayed_for_non_yum_repo(self):
        """Verify that non-YUM repositories cannot be created with download
        policy

        @id: 47d55251-5f89-443d-b980-a441da34e205

        @Assert: Dropdown for download policy is not displayed for non-yum repo
        """
        non_yum_repo_types = [
            repo_type for repo_type in REPO_TYPE.values()
            if repo_type != 'yum'
        ]
        with Session(self.browser):
            for content_type in non_yum_repo_types:
                self.products.search_and_click(self.session_prod.name)
                with self.subTest(content_type):
                    self.repository.navigate_to_entity()
                    self.repository.click(locators['repo.new'])
                    self.repository.assign_value(
                        common_locators['name'], gen_string('alphanumeric'))
                    self.repository.assign_value(
                        locators['repo.type'], content_type)
                    self.assertIsNone(
                        self.repository.find_element(
                            locators['repo.download_policy']
                        )
                    )

    @tier2
    def test_positive_srpm_sync(self):
        """Synchronize repository with SRPMs

        @id: 1967a540-a265-4046-b87b-627524b63688

        @Assert: srpms can be listed in repository
        """
        product = entities.Product(organization=self.session_org).create()
        repo_name = gen_string('alphanumeric')
        with Session(self.browser) as session:
            self.products.search(product.name).click()
            make_repository(
                session,
                name=repo_name,
                url=FAKE_YUM_SRPM_REPO,
            )
            self.assertIsNotNone(self.repository.search(repo_name))
            self.setup_navigate_syncnow(
                session,
                product.name,
                repo_name,
            )
            self.assertTrue(self.prd_sync_is_ok(repo_name))
        result = ssh.command(
            'ls /var/lib/pulp/published/yum/https/repos/{}/Library'
            '/custom/{}/{}/ | grep .src.rpm'
            .format(
                self.session_org.label,
                product.label,
                repo_name,
            )
        )
        self.assertEqual(result.return_code, 0)
        self.assertGreaterEqual(len(result.stdout), 1)

    @tier2
    def test_positive_srpm_sync_publish_cv(self):
        """Synchronize repository with SRPMs, add repository to content view
        and publish content view

        @id: 2a57cbde-c616-440d-8bcb-6e18bd2d5c5f

        @Assert: srpms can be listed in content view
        """
        product = entities.Product(organization=self.session_org).create()
        repo_name = gen_string('alphanumeric')
        cv_name = gen_string('alphanumeric')
        with Session(self.browser) as session:
            self.products.search(product.name).click()
            make_repository(
                session,
                name=repo_name,
                url=FAKE_YUM_SRPM_REPO,
            )
            self.assertIsNotNone(self.repository.search(repo_name))
            self.setup_navigate_syncnow(
                session,
                product.name,
                repo_name,
            )
            self.assertTrue(self.prd_sync_is_ok(repo_name))

            make_contentview(session, org=self.session_org.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            self.content_views.add_remove_repos(cv_name, [repo_name])
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success_sub_form']))
            self.content_views.publish(cv_name)
            self.assertIsNotNone(self.content_views.wait_until_element
                                 (common_locators['alert.success_sub_form']))
        result = ssh.command(
            'ls /var/lib/pulp/published/yum/https/repos/{}/content_views/{}'
            '/1.0/custom/{}/{}/ | grep .src.rpm'
            .format(
                self.session_org.label,
                cv_name,
                product.label,
                repo_name,
            )
        )
        self.assertEqual(result.return_code, 0)
        self.assertGreaterEqual(len(result.stdout), 1)

    @tier2
    def test_positive_srpm_sync_publish_promote_cv(self):
        """Synchronize repository with SRPMs, add repository to content view,
        publish and promote content view to lifecycle environment

        @id: 4563d1c1-cdce-4838-a67f-c0a5d4e996a6

        @Assert: srpms can be listed in content view in proper lifecycle
        environment
        """
        lce = entities.LifecycleEnvironment(
            organization=self.session_org).create()
        product = entities.Product(organization=self.session_org).create()
        repo_name = gen_string('alphanumeric')
        cv_name = gen_string('alphanumeric')
        with Session(self.browser) as session:
            self.products.search(product.name).click()
            make_repository(
                session,
                name=repo_name,
                url=FAKE_YUM_SRPM_REPO,
            )
            self.assertIsNotNone(self.repository.search(repo_name))
            self.setup_navigate_syncnow(
                session,
                product.name,
                repo_name,
            )
            self.assertTrue(self.prd_sync_is_ok(repo_name))

            make_contentview(session, org=self.session_org.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            self.content_views.add_remove_repos(cv_name, [repo_name])
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success_sub_form']))
            self.content_views.publish(cv_name)
            self.assertIsNotNone(self.content_views.wait_until_element
                                 (common_locators['alert.success_sub_form']))
            self.content_views.promote(cv_name, 'Version 1', lce.name)
            self.assertIsNotNone(self.content_views.wait_until_element
                                 (common_locators['alert.success_sub_form']))
        result = ssh.command(
            'ls /var/lib/pulp/published/yum/https/repos/{}/{}/{}/custom/{}/{}/'
            ' | grep .src.rpm'
            .format(
                self.session_org.label,
                lce.name,
                cv_name,
                product.label,
                repo_name,
            )
        )
        self.assertEqual(result.return_code, 0)
        self.assertGreaterEqual(len(result.stdout), 1)

    @tier2
    def test_positive_drpm_sync(self):
        """Synchronize repository with DRPMs

        @id: 5e703d9a-ea26-4062-9d5c-d31bfbe87417

        @Assert: drpms can be listed in repository
        """
        product = entities.Product(organization=self.session_org).create()
        repo_name = gen_string('alphanumeric')
        with Session(self.browser) as session:
            self.products.search(product.name).click()
            make_repository(
                session,
                name=repo_name,
                url=FAKE_YUM_DRPM_REPO,
            )
            self.assertIsNotNone(self.repository.search(repo_name))
            self.setup_navigate_syncnow(
                session,
                product.name,
                repo_name,
            )
            self.assertTrue(self.prd_sync_is_ok(repo_name))
        result = ssh.command(
            'ls /var/lib/pulp/published/yum/https/repos/{}/Library'
            '/custom/{}/{}/drpms/ | grep .drpm'
            .format(
                self.session_org.label,
                product.label,
                repo_name,
            )
        )
        self.assertEqual(result.return_code, 0)
        self.assertGreaterEqual(len(result.stdout), 1)

    @tier2
    def test_positive_drpm_sync_publish_cv(self):
        """Synchronize repository with DRPMs, add repository to content view
        and publish content view

        @id: cffa862c-f972-4aa4-96b2-5a4513cb3eef

        @Assert: drpms can be listed in content view
        """
        product = entities.Product(organization=self.session_org).create()
        repo_name = gen_string('alphanumeric')
        cv_name = gen_string('alphanumeric')
        with Session(self.browser) as session:
            self.products.search(product.name).click()
            make_repository(
                session,
                name=repo_name,
                url=FAKE_YUM_DRPM_REPO,
            )
            self.assertIsNotNone(self.repository.search(repo_name))
            self.setup_navigate_syncnow(
                session,
                product.name,
                repo_name,
            )
            self.assertTrue(self.prd_sync_is_ok(repo_name))

            make_contentview(session, org=self.session_org.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            self.content_views.add_remove_repos(cv_name, [repo_name])
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success_sub_form']))
            self.content_views.publish(cv_name)
            self.assertIsNotNone(self.content_views.wait_until_element
                                 (common_locators['alert.success_sub_form']))
        result = ssh.command(
            'ls /var/lib/pulp/published/yum/https/repos/{}/content_views/{}'
            '/1.0/custom/{}/{}/drpms/ | grep .drpm'
            .format(
                self.session_org.label,
                cv_name,
                product.label,
                repo_name,
            )
        )
        self.assertEqual(result.return_code, 0)
        self.assertGreaterEqual(len(result.stdout), 1)

    @tier2
    def test_positive_drpm_sync_publish_promote_cv(self):
        """Synchronize repository with DRPMs, add repository to content view,
        publish and promote content view to lifecycle environment

        @id: e33ee07c-4677-4be8-bd53-73689edfda34

        @Assert: drpms can be listed in content view in proper lifecycle
        environment
        """
        lce = entities.LifecycleEnvironment(
            organization=self.session_org).create()
        product = entities.Product(organization=self.session_org).create()
        repo_name = gen_string('alphanumeric')
        cv_name = gen_string('alphanumeric')
        with Session(self.browser) as session:
            self.products.search(product.name).click()
            make_repository(
                session,
                name=repo_name,
                url=FAKE_YUM_DRPM_REPO,
            )
            self.assertIsNotNone(self.repository.search(repo_name))
            self.setup_navigate_syncnow(
                session,
                product.name,
                repo_name,
            )
            self.assertTrue(self.prd_sync_is_ok(repo_name))

            make_contentview(session, org=self.session_org.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            self.content_views.add_remove_repos(cv_name, [repo_name])
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success_sub_form']))
            self.content_views.publish(cv_name)
            self.assertIsNotNone(self.content_views.wait_until_element
                                 (common_locators['alert.success_sub_form']))
            self.content_views.promote(cv_name, 'Version 1', lce.name)
            self.assertIsNotNone(self.content_views.wait_until_element
                                 (common_locators['alert.success_sub_form']))
        result = ssh.command(
            'ls /var/lib/pulp/published/yum/https/repos/{}/{}/{}/custom/{}/{}'
            '/drpms/ | grep .drpm'
            .format(
                self.session_org.label,
                lce.name,
                cv_name,
                product.label,
                repo_name,
            )
        )
        self.assertEqual(result.return_code, 0)
        self.assertGreaterEqual(len(result.stdout), 1)
