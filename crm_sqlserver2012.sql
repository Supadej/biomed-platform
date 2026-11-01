-- CRM persistence staging schema, SQL Server 2012 compatible.
-- This is a migration target, NOT a runtime database adapter.
-- Run in the chosen existing database after reviewing backups and naming.
IF OBJECT_ID(N'dbo.CrmRecords', N'U') IS NULL
 CREATE TABLE dbo.CrmRecords(Entity nvarchar(64) NOT NULL,RecordId int NOT NULL,Payload nvarchar(max) NOT NULL,Version int NOT NULL DEFAULT 1,Deleted bit NOT NULL DEFAULT 0,CONSTRAINT PK_CrmRecords PRIMARY KEY(Entity,RecordId));
IF OBJECT_ID(N'dbo.CrmIdentity', N'U') IS NULL
 CREATE TABLE dbo.CrmIdentity(PortalUserId nvarchar(200) NOT NULL PRIMARY KEY,CrmUserId int NOT NULL UNIQUE);
IF OBJECT_ID(N'dbo.CrmAudit', N'U') IS NULL
 CREATE TABLE dbo.CrmAudit(Id int NOT NULL PRIMARY KEY,AtUtc nvarchar(48) NOT NULL,Actor nvarchar(200) NOT NULL,Entity nvarchar(64) NOT NULL,RecordId int NULL,Action nvarchar(64) NOT NULL,Detail nvarchar(max) NOT NULL);
IF OBJECT_ID(N'dbo.CrmFiles', N'U') IS NULL
 CREATE TABLE dbo.CrmFiles(Id uniqueidentifier NOT NULL PRIMARY KEY,Name nvarchar(512) NOT NULL,Mime nvarchar(256) NOT NULL,Content varbinary(max) NOT NULL,OwnerId nvarchar(200) NOT NULL);
IF OBJECT_ID(N'dbo.CrmLinks', N'U') IS NULL
 CREATE TABLE dbo.CrmLinks(Source nvarchar(32) NOT NULL,SourceId nvarchar(256) NOT NULL,Entity nvarchar(64) NOT NULL,RecordId int NOT NULL,CONSTRAINT PK_CrmLinks PRIMARY KEY(Source,SourceId,Entity));
IF OBJECT_ID(N'dbo.CrmBridgeConfig', N'U') IS NULL
 CREATE TABLE dbo.CrmBridgeConfig(Direction nvarchar(32) NOT NULL PRIMARY KEY,Payload nvarchar(max) NOT NULL,Revision int NOT NULL);
IF OBJECT_ID(N'dbo.CrmBridgeRuns', N'U') IS NULL
 CREATE TABLE dbo.CrmBridgeRuns(Id int NOT NULL PRIMARY KEY,Direction nvarchar(32) NOT NULL,AtUtc nvarchar(48) NOT NULL,Actor nvarchar(200) NOT NULL,Digest nvarchar(64) NOT NULL,Result nvarchar(max) NOT NULL);
