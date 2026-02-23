-- FROM: https://github.com/FreeRADIUS/freeradius-server/blob/master/raddb/mods-config/sql/main/postgresql/schema.sql

--
-- $Id$
--
-- Postgresql schema for FreeRADIUS
--

--
-- Table structure for table 'radacct'
--
CREATE TABLE IF NOT EXISTS radacct (
	radacctid		bigserial PRIMARY KEY,
	acctsessionid		text NOT NULL,
	acctuniqueid		text NOT NULL UNIQUE,
	username		text,
	groupname		text,
	realm			text,
	nasipaddress		inet NOT NULL,
	nasportid		text,
	nasporttype		text,
	acctstarttime		timestamp with time zone,
	acctupdatetime		timestamp with time zone,
	acctstoptime		timestamp with time zone,
	acctinterval		bigint,
	acctsessiontime		bigint,
	acctauthentic		text,
	connectinfo_start	text,
	connectinfo_stop	text,
	acctinputoctets		bigint,
	acctoutputoctets	bigint,
	calledstationid		text,
	callingstationid	text,
	acctterminatecause	text,
	servicetype		text,
	framedprotocol		text,
	framedipaddress		inet,
	framedipv6address	inet,
	framedipv6prefix	inet,
	framedinterfaceid	text,
	delegatedipv6prefix	inet,
	class 			text
);
-- This index may be useful..
-- CREATE UNIQUE INDEX radacct_whoson on radacct (AcctStartTime, nasipaddress);

-- For use by update-, stop- and simul_* queries
CREATE INDEX radacct_active_session_idx ON radacct (acctuniqueid) WHERE acctstoptime IS NULL;

-- Add if you you regularly have to replay packets
-- CREATE INDEX radacct_session_idx ON radacct (AcctUniqueId);

-- For use by onoff-
CREATE INDEX radacct_bulk_close ON radacct (nasipaddress, acctstarttime) WHERE acctstoptime IS NULL;

-- For use by cleanup scripts
-- Works well for timeout queries, where ((acctstoptime IS NULL) AND (acctupdatetime < (now() - '1 day'::interval)))
-- as well as removing old sessions from the database.
--
-- Although at first glance it appears where an index on acctupdatetime with condition WHERE acctstoptime IS NULL;
-- would be more effective, the query planner refused to use the index (for some unknown reason), and doing it this
-- way allows the index to be used for both timeouts and cleanup.
CREATE INDEX radacct_bulk_timeout ON radacct (acctstoptime NULLS FIRST, acctupdatetime);

-- and for common statistic queries:
CREATE INDEX radacct_start_user_idx ON radacct (acctstarttime, username);
-- and, optionally
-- CREATE INDEX radacct_stop_user_idx ON radacct (acctstoptime, username);

--
-- Table structure for table 'radpostauth'
--
CREATE TABLE radpostauth (
	id			bigserial PRIMARY KEY,
	username		text NOT NULL,
	pass			text,
	reply			text,
	calledstationid		text,
	callingstationid	text,
	authdate		timestamp with time zone NOT NULL default now(),
	class			text
);

--
-- Table structure for table 'nas'
--
CREATE TABLE nas (
	id			serial PRIMARY KEY,
	nasname			text NOT NULL,
	shortname		text NOT NULL,
	type			text NOT NULL DEFAULT 'other',
	ports			integer,
	secret			text NOT NULL,
	server			text,
	community		text,
	description		text,
	require_ma		text NOT NULL DEFAULT 'auto',
	limit_proxy_state	text NOT NULL DEFAULT 'auto'
);
create index nas_nasname on nas (nasname);

/*
 * Table structure for table 'nasreload'
 */
CREATE TABLE IF NOT EXISTS nasreload (
	nasipaddress		inet PRIMARY KEY,
	reloadtime		timestamp with time zone NOT NULL
);