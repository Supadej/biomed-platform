-- SQL Server 2012 compatible target for the current application workspace model.
-- Avoid JSON-specific SQL operators; workspace payloads are NVARCHAR(MAX).
IF OBJECT_ID(N'dbo.BiomedWorkspace',N'U') IS NULL
CREATE TABLE dbo.BiomedWorkspace(
  WorkspaceKey NVARCHAR(160) NOT NULL CONSTRAINT PK_BiomedWorkspace PRIMARY KEY,
  Payload NVARCHAR(MAX) NULL,
  Revision BIGINT NOT NULL CONSTRAINT DF_BiomedWorkspace_Revision DEFAULT(1),
  UpdatedAt DATETIME2(0) NOT NULL CONSTRAINT DF_BiomedWorkspace_UpdatedAt DEFAULT(SYSUTCDATETIME())
);
IF OBJECT_ID(N'dbo.BiomedAccount',N'U') IS NULL
CREATE TABLE dbo.BiomedAccount(
  AccountId CHAR(32) NOT NULL CONSTRAINT PK_BiomedAccount PRIMARY KEY,
  Email NVARCHAR(254) NOT NULL,
  DisplayName NVARCHAR(200) NOT NULL,
  RoleName NVARCHAR(80) NOT NULL,
  PortalUserId NVARCHAR(80) NOT NULL,
  PasswordHash VARBINARY(32) NOT NULL,
  PasswordSalt VARBINARY(16) NOT NULL,
  PasswordIterations INT NOT NULL,
  Disabled BIT NOT NULL CONSTRAINT DF_BiomedAccount_Disabled DEFAULT(0),
  FailedAttempts INT NOT NULL CONSTRAINT DF_BiomedAccount_Failed DEFAULT(0),
  LockedUntil BIGINT NOT NULL CONSTRAINT DF_BiomedAccount_Locked DEFAULT(0),
  CreatedAt DATETIME2(0) NOT NULL CONSTRAINT DF_BiomedAccount_Created DEFAULT(SYSUTCDATETIME()),
  CONSTRAINT UQ_BiomedAccount_Email UNIQUE(Email)
);
IF OBJECT_ID(N'dbo.BiomedSession',N'U') IS NULL
CREATE TABLE dbo.BiomedSession(
  TokenHash CHAR(64) NOT NULL CONSTRAINT PK_BiomedSession PRIMARY KEY,
  AccountId CHAR(32) NOT NULL,
  ExpiresAt BIGINT NOT NULL,
  CreatedAt BIGINT NOT NULL,
  CONSTRAINT FK_BiomedSession_Account FOREIGN KEY(AccountId) REFERENCES dbo.BiomedAccount(AccountId) ON DELETE CASCADE
);
IF NOT EXISTS(SELECT 1 FROM sys.indexes WHERE name=N'IX_BiomedSession_ExpiresAt' AND object_id=OBJECT_ID(N'dbo.BiomedSession')) CREATE INDEX IX_BiomedSession_ExpiresAt ON dbo.BiomedSession(ExpiresAt);
IF OBJECT_ID(N'dbo.BiomedDocument',N'U') IS NULL
CREATE TABLE dbo.BiomedDocument(
  DocumentId NVARCHAR(100) NOT NULL CONSTRAINT PK_BiomedDocument PRIMARY KEY,
  DocumentKind NVARCHAR(60) NOT NULL,
  DocumentReference NVARCHAR(100) NULL,
  DocumentStatus NVARCHAR(40) NULL,
  SourceDocumentId NVARCHAR(100) NULL,
  Payload NVARCHAR(MAX) NOT NULL
);
IF NOT EXISTS(SELECT 1 FROM sys.indexes WHERE name=N'IX_BiomedDocument_KindStatus' AND object_id=OBJECT_ID(N'dbo.BiomedDocument')) CREATE INDEX IX_BiomedDocument_KindStatus ON dbo.BiomedDocument(DocumentKind,DocumentStatus);
IF NOT EXISTS(SELECT 1 FROM sys.indexes WHERE name=N'IX_BiomedDocument_Source' AND object_id=OBJECT_ID(N'dbo.BiomedDocument')) CREATE INDEX IX_BiomedDocument_Source ON dbo.BiomedDocument(SourceDocumentId);
IF OBJECT_ID(N'dbo.BiomedDocumentLine',N'U') IS NULL
CREATE TABLE dbo.BiomedDocumentLine(
  DocumentId NVARCHAR(100) NOT NULL,
  LinePosition INT NOT NULL,
  ProductId NVARCHAR(100) NULL,
  Payload NVARCHAR(MAX) NOT NULL,
  CONSTRAINT PK_BiomedDocumentLine PRIMARY KEY(DocumentId,LinePosition),
  CONSTRAINT FK_BiomedDocumentLine_Document FOREIGN KEY(DocumentId) REFERENCES dbo.BiomedDocument(DocumentId) ON DELETE CASCADE
);
IF OBJECT_ID(N'dbo.BiomedMasterRecord',N'U') IS NULL
CREATE TABLE dbo.BiomedMasterRecord(
  Category NVARCHAR(60) NOT NULL,
  RecordId NVARCHAR(120) NOT NULL,
  Payload NVARCHAR(MAX) NOT NULL,
  CONSTRAINT PK_BiomedMasterRecord PRIMARY KEY(Category,RecordId)
);
IF OBJECT_ID(N'dbo.BiomedStockRecord',N'U') IS NULL
CREATE TABLE dbo.BiomedStockRecord(
  Category NVARCHAR(60) NOT NULL,
  Position INT NOT NULL,
  Payload NVARCHAR(MAX) NOT NULL,
  CONSTRAINT PK_BiomedStockRecord PRIMARY KEY(Category,Position)
);
IF OBJECT_ID(N'dbo.BiomedAudit',N'U') IS NULL
CREATE TABLE dbo.BiomedAudit(
  AuditId BIGINT IDENTITY(1,1) NOT NULL CONSTRAINT PK_BiomedAudit PRIMARY KEY,
  AccountId CHAR(32) NULL,
  ActionName NVARCHAR(120) NOT NULL,
  Reference NVARCHAR(160) NULL,
  EventAt DATETIME2(0) NOT NULL CONSTRAINT DF_BiomedAudit_EventAt DEFAULT(SYSUTCDATETIME()),
  Detail NVARCHAR(MAX) NULL
);
GO

IF OBJECT_ID(N'dbo.BiomedUserPreference',N'U') IS NULL
CREATE TABLE dbo.BiomedUserPreference(
 AccountId NVARCHAR(64) NOT NULL,
 SystemName NVARCHAR(16) NOT NULL,
 Payload NVARCHAR(MAX) NOT NULL,
 CONSTRAINT PK_BiomedUserPreference PRIMARY KEY(AccountId,SystemName)
);
GO
