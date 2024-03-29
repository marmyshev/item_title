# -*- coding: utf-8 -*-
# vim: autoindent shiftwidth=4 expandtab textwidth=120 tabstop=4 softtabstop=4

###############################################################################
# OpenLP - Open Source Lyrics Projection                                      #
# --------------------------------------------------------------------------- #
# Copyright (c) 2008-2013 Raoul Snyman                                        #
# Portions copyright (c) 2008-2013 Tim Bentley, Gerald Britton, Jonathan      #
# Corwin, Samuel Findlay, Michael Gorven, Scott Guerrieri, Matthias Hub,      #
# Meinert Jordan, Armin Köhler, Erik Lundin, Edwin Lunando, Brian T. Meyer.   #
# Joshua Miller, Stevan Pettit, Andreas Preikschat, Mattias Põldaru,          #
# Christian Richter, Philip Ridout, Simon Scudder, Jeffrey Smith,             #
# Maikel Stuivenberg, Martin Thompson, Jon Tibble, Dave Warnock,              #
# Frode Woldsund, Martin Zibricky, Patrick Zimmermann                         #
# --------------------------------------------------------------------------- #
# This program is free software; you can redistribute it and/or modify it     #
# under the terms of the GNU General Public License as published by the Free  #
# Software Foundation; version 2 of the License.                              #
#                                                                             #
# This program is distributed in the hope that it will be useful, but WITHOUT #
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or       #
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for    #
# more details.                                                               #
#                                                                             #
# You should have received a copy of the GNU General Public License along     #
# with this program; if not, write to the Free Software Foundation, Inc., 59  #
# Temple Place, Suite 330, Boston, MA 02111-1307 USA                          #
###############################################################################

"""
The :mod:`db` module provides the core database functionality for OpenLP
"""
import logging
import os
from urllib.parse import quote_plus as urlquote

from sqlalchemy import Table, MetaData, Column, types, create_engine
from sqlalchemy.exc import SQLAlchemyError, InvalidRequestError, DBAPIError, OperationalError
from sqlalchemy.orm import scoped_session, sessionmaker, mapper
from sqlalchemy.pool import NullPool
from alembic.migration import MigrationContext
from alembic.operations import Operations

from openlp.core.lib import translate, Settings
from openlp.core.lib.ui import critical_error_message_box
from openlp.core.utils import AppLocation, delete_file

log = logging.getLogger(__name__)


def init_db(url, auto_flush=True, auto_commit=False):
    """
    Initialise and return the session and metadata for a database

    ``url``
        The database to initialise connection with

    ``auto_flush``
        Sets the flushing behaviour of the session

    ``auto_commit``
        Sets the commit behaviour of the session
    """
    engine = create_engine(url, poolclass=NullPool)
    metadata = MetaData(bind=engine)
    session = scoped_session(sessionmaker(autoflush=auto_flush, autocommit=auto_commit, bind=engine))
    return session, metadata


def get_upgrade_op(session):
    """
    Create a migration context and an operations object for performing upgrades.

    ``session``
        The SQLAlchemy session object.
    """
    context = MigrationContext.configure(session.bind.connect())
    return Operations(context)


def upgrade_db(url, upgrade):
    """
    Upgrade a database.

    ``url``
        The url of the database to upgrade.

    ``upgrade``
        The python module that contains the upgrade instructions.
    """
    session, metadata = init_db(url)

    class Metadata(BaseModel):
        """
        Provides a class for the metadata table.
        """
        pass

    metadata_table = Table('metadata', metadata,
        Column('key', types.Unicode(64), primary_key=True),
        Column('value', types.UnicodeText(), default=None)
    )
    metadata_table.create(checkfirst=True)
    mapper(Metadata, metadata_table)
    version_meta = session.query(Metadata).get('version')
    if version_meta is None:
        version_meta = Metadata.populate(key='version', value='0')
        session.add(version_meta)
        version = 0
    else:
        version = int(version_meta.value)
    if version > upgrade.__version__:
        return version, upgrade.__version__
    version += 1
    try:
        while hasattr(upgrade, 'upgrade_%d' % version):
            log.debug('Running upgrade_%d', version)
            try:
                upgrade_func = getattr(upgrade, 'upgrade_%d' % version)
                upgrade_func(session, metadata)
                session.commit()
                # Update the version number AFTER a commit so that we are sure the previous transaction happened
                version_meta.value = str(version)
                session.commit()
                version += 1
            except (SQLAlchemyError, DBAPIError):
                log.exception('Could not run database upgrade script "upgrade_%s", upgrade process has been halted.',
                              version)
                break
    except (SQLAlchemyError, DBAPIError):
        version_meta = Metadata.populate(key='version', value=int(upgrade.__version__))
        session.commit()
    return int(version_meta.value), upgrade.__version__


def delete_database(plugin_name, db_file_name=None):
    """
    Remove a database file from the system.

    ``plugin_name``
        The name of the plugin to remove the database for

    ``db_file_name``
        The database file name. Defaults to None resulting in the plugin_name being used.
    """
    db_file_path = None
    if db_file_name:
        db_file_path = os.path.join(AppLocation.get_section_data_path(plugin_name), db_file_name)
    else:
        db_file_path = os.path.join(AppLocation.get_section_data_path(plugin_name), plugin_name)
    return delete_file(db_file_path)


class BaseModel(object):
    """
    BaseModel provides a base object with a set of generic functions
    """
    @classmethod
    def populate(cls, **kwargs):
        """
        Creates an instance of a class and populates it, returning the instance
        """
        instance = cls()
        for key, value in kwargs.items():
            instance.__setattr__(key, value)
        return instance


class Manager(object):
    """
    Provide generic object persistence management
    """
    def __init__(self, plugin_name, init_schema, db_file_name=None, upgrade_mod=None):
        """
        Runs the initialisation process that includes creating the connection to the database and the tables if they do
        not exist.

        ``plugin_name``
            The name to setup paths and settings section names

        ``init_schema``
            The init_schema function for this database

        ``upgrade_schema``
            The upgrade_schema function for this database

        ``db_file_name``
            The file name to use for this database. Defaults to None resulting in the plugin_name being used.
        """
        settings = Settings()
        settings.beginGroup(plugin_name)
        self.db_url = ''
        self.is_dirty = False
        self.session = None
        db_type = settings.value('db type')
        if db_type == 'sqlite':
            if db_file_name:
                self.db_url = 'sqlite:///%s/%s' % (AppLocation.get_section_data_path(plugin_name), db_file_name)
            else:
                self.db_url = 'sqlite:///%s/%s.sqlite' % (AppLocation.get_section_data_path(plugin_name), plugin_name)
        else:
            self.db_url = '%s://%s:%s@%s/%s' % (db_type,
                urlquote(settings.value('db username')),
                urlquote(settings.value('db password')),
                urlquote(settings.value('db hostname')),
                urlquote(settings.value('db database')))
            if db_type == 'mysql':
                db_encoding = settings.value('db encoding')
                self.db_url += '?charset=%s' % urlquote(db_encoding)
        settings.endGroup()
        if upgrade_mod:
            db_ver, up_ver = upgrade_db(self.db_url, upgrade_mod)
            if db_ver > up_ver:
                critical_error_message_box(
                    translate('OpenLP.Manager', 'Database Error'),
                    translate('OpenLP.Manager', 'The database being loaded was created in a more recent version of '
                        'OpenLP. The database is version %d, while OpenLP expects version %d. The database will not '
                        'be loaded.\n\nDatabase: %s') % (db_ver, up_ver, self.db_url)
                )
                return
        try:
            self.session = init_schema(self.db_url)
        except (SQLAlchemyError, DBAPIError):
            log.exception('Error loading database: %s', self.db_url)
            critical_error_message_box(
                translate('OpenLP.Manager', 'Database Error'),
                translate('OpenLP.Manager', 'OpenLP cannot load your database.\n\nDatabase: %s') % self.db_url
            )

    def save_object(self, object_instance, commit=True):
        """
        Save an object to the database

        ``object_instance``
            The object to save

        ``commit``
            Commit the session with this object
        """
        for try_count in range(3):
            try:
                self.session.add(object_instance)
                if commit:
                    self.session.commit()
                self.is_dirty = True
                return True
            except OperationalError:
                # This exception clause is for users running MySQL which likes to terminate connections on its own
                # without telling anyone. See bug #927473. However, other dbms can raise it, usually in a
                # non-recoverable way. So we only retry 3 times.
                log.exception('Probably a MySQL issue - "MySQL has gone away"')
                self.session.rollback()
                if try_count >= 2:
                    raise
            except InvalidRequestError:
                self.session.rollback()
                log.exception('Object list save failed')
                return False
            except:
                self.session.rollback()
                raise

    def save_objects(self, object_list, commit=True):
        """
        Save a list of objects to the database

        ``object_list``
            The list of objects to save

        ``commit``
            Commit the session with this object
        """
        for try_count in range(3):
            try:
                self.session.add_all(object_list)
                if commit:
                    self.session.commit()
                self.is_dirty = True
                return True
            except OperationalError:
                # This exception clause is for users running MySQL which likes to terminate connections on its own
                # without telling anyone. See bug #927473. However, other dbms can raise it, usually in a
                # non-recoverable way. So we only retry 3 times.
                log.exception('Probably a MySQL issue, "MySQL has gone away"')
                self.session.rollback()
                if try_count >= 2:
                    raise
            except InvalidRequestError:
                self.session.rollback()
                log.exception('Object list save failed')
                return False
            except:
                self.session.rollback()
                raise

    def get_object(self, object_class, key=None):
        """
        Return the details of an object

        ``object_class``
            The type of object to return

        ``key``
            The unique reference or primary key for the instance to return
        """
        if not key:
            return object_class()
        else:
            for try_count in range(3):
                try:
                    return self.session.query(object_class).get(key)
                except OperationalError:
                    # This exception clause is for users running MySQL which likes to terminate connections on its own
                    # without telling anyone. See bug #927473. However, other dbms can raise it, usually in a
                    # non-recoverable way. So we only retry 3 times.
                    log.exception('Probably a MySQL issue, "MySQL has gone away"')
                    if try_count >= 2:
                        raise

    def get_object_filtered(self, object_class, filter_clause):
        """
        Returns an object matching specified criteria

        ``object_class``
            The type of object to return

        ``filter_clause``
            The criteria to select the object by
        """
        for try_count in range(3):
            try:
                return self.session.query(object_class).filter(filter_clause).first()
            except OperationalError:
                # This exception clause is for users running MySQL which likes to terminate connections on its own
                # without telling anyone. See bug #927473. However, other dbms can raise it, usually in a
                # non-recoverable way. So we only retry 3 times.
                log.exception('Probably a MySQL issue, "MySQL has gone away"')
                if try_count >= 2:
                    raise

    def get_all_objects(self, object_class, filter_clause=None, order_by_ref=None):
        """
        Returns all the objects from the database

        ``object_class``
            The type of objects to return

        ``filter_clause``
            The filter governing selection of objects to return. Defaults to None.

        ``order_by_ref``
            Any parameters to order the returned objects by. Defaults to None.
        """
        query = self.session.query(object_class)
        if filter_clause is not None:
            query = query.filter(filter_clause)
        if isinstance(order_by_ref, list):
            query = query.order_by(*order_by_ref)
        elif order_by_ref is not None:
            query = query.order_by(order_by_ref)
        for try_count in range(3):
            try:
                return query.all()
            except OperationalError:
                # This exception clause is for users running MySQL which likes to terminate connections on its own
                # without telling anyone. See bug #927473. However, other dbms can raise it, usually in a
                # non-recoverable way. So we only retry 3 times.
                log.exception('Probably a MySQL issue, "MySQL has gone away"')
                if try_count >= 2:
                    raise

    def get_object_count(self, object_class, filter_clause=None):
        """
        Returns a count of the number of objects in the database.

        ``object_class``
            The type of objects to return.

        ``filter_clause``
            The filter governing selection of objects to return. Defaults to None.
        """
        query = self.session.query(object_class)
        if filter_clause is not None:
            query = query.filter(filter_clause)
        for try_count in range(3):
            try:
                return query.count()
            except OperationalError:
                # This exception clause is for users running MySQL which likes to terminate connections on its own
                # without telling anyone. See bug #927473. However, other dbms can raise it, usually in a
                # non-recoverable way. So we only retry 3 times.
                log.exception('Probably a MySQL issue, "MySQL has gone away"')
                if try_count >= 2:
                    raise

    def delete_object(self, object_class, key):
        """
        Delete an object from the database

        ``object_class``
            The type of object to delete

        ``key``
            The unique reference or primary key for the instance to be deleted
        """
        if key != 0:
            object_instance = self.get_object(object_class, key)
            for try_count in range(3):
                try:
                    self.session.delete(object_instance)
                    self.session.commit()
                    self.is_dirty = True
                    return True
                except OperationalError:
                    # This exception clause is for users running MySQL which likes to terminate connections on its own
                    # without telling anyone. See bug #927473. However, other dbms can raise it, usually in a
                    # non-recoverable way. So we only retry 3 times.
                    log.exception('Probably a MySQL issue, "MySQL has gone away"')
                    self.session.rollback()
                    if try_count >= 2:
                        raise
                except InvalidRequestError:
                    self.session.rollback()
                    log.exception('Failed to delete object')
                    return False
                except:
                    self.session.rollback()
                    raise
        else:
            return True

    def delete_all_objects(self, object_class, filter_clause=None):
        """
        Delete all object records. This method should only be used for simple tables and **not** ones with
        relationships. The relationships are not deleted from the database and this will lead to database corruptions.

        ``object_class``
            The type of object to delete

        ``filter_clause``
            The filter governing selection of objects to return. Defaults to None.
        """
        for try_count in range(3):
            try:
                query = self.session.query(object_class)
                if filter_clause is not None:
                    query = query.filter(filter_clause)
                query.delete(synchronize_session=False)
                self.session.commit()
                self.is_dirty = True
                return True
            except OperationalError:
                # This exception clause is for users running MySQL which likes to terminate connections on its own
                # without telling anyone. See bug #927473. However, other dbms can raise it, usually in a
                # non-recoverable way. So we only retry 3 times.
                log.exception('Probably a MySQL issue, "MySQL has gone away"')
                self.session.rollback()
                if try_count >= 2:
                    raise
            except InvalidRequestError:
                self.session.rollback()
                log.exception('Failed to delete %s records', object_class.__name__)
                return False
            except:
                self.session.rollback()
                raise

    def finalise(self):
        """
        VACUUM the database on exit.
        """
        if self.is_dirty:
            engine = create_engine(self.db_url)
            if self.db_url.startswith('sqlite'):
                engine.execute("vacuum")
