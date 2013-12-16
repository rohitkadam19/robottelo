#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from robottelo.cli.base import Base


class Domain(Base):

    def __init__(self):
        self.command_base = "domain"

    def delete_parameter(self, options=None):
        """
        Delete parameter for a domain.
        """

        self.command_sub = "delete_parameter"

        result = self.execute(self._construct_command(options))

        return False if result.stderr else True

    def set_parameter(self, options=None):
        """
        Create or update parameter for a domain.
        """

        self.command_sub = "set_parameter"

        result = self.execute(self._construct_command(options))

        return False if result.stderr else True