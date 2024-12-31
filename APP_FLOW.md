# Terran POS System - Application Flow

This document describes the flow of the Terran POS System application, including window management, user authentication, and session handling.

## Application Startup Flow

```mermaid
graph TD
    A[Application Start] --> B[Initialize Database]
    B --> C[Create Main Window]
    C --> D[Initialize UI Components]
    D --> E[Hide Main Window]
    E --> F[Show Login Window]
    F --> G{Login Attempt}
    G -->|Success| H[Hide Login Window]
    H --> I[Show Main Window]
    G -->|Failure| J[Show Error Message]
    J --> F
    I --> K[Update Menu Permissions]
    K --> L[Start Session Timer]
```

## Session Management Flow

```mermaid
graph TD
    A[Active Session] --> B[Session Timer Check]
    B --> C{Session Valid?}
    C -->|Yes| D[Continue Session]
    D --> B
    C -->|No| E[Show Timeout Message]
    E --> F[Logout User]
    F --> G[Hide Main Window]
    G --> H[Show Login Window]
```

## Window Hierarchy

```mermaid
graph TD
    A[Main Window] --> B[Login Window]
    A --> C[POS Window]
    A --> D[Inventory Window]
    A --> E[Reports Window]
    A --> F[Backup Window]
    A --> G[User Management Window]
    A --> H[Company Info Dialog]
    A --> I[Change Password Dialog]
```

## User Authentication Flow

```mermaid
graph TD
    A[Login Window] --> B{Check Credentials}
    B -->|Valid| C[Create Session]
    C --> D[Log Activity]
    D --> E{First Login?}
    E -->|Yes| F[Show Password Change]
    F -->|Success| G[Show Main Window]
    E -->|No| G
    B -->|Invalid| H[Show Error]
    H --> A
```

## Permission Check Flow

```mermaid
graph TD
    A[User Action] --> B{Check Permission}
    B -->|Has Permission| C[Execute Action]
    B -->|No Permission| D[Show Access Denied]
    C --> E[Log Activity]
```

## Window States

| Window | Initial State | Post-Login | On Logout |
|--------|--------------|------------|-----------|
| Main Window | Hidden | Visible | Hidden |
| Login Window | Visible | Hidden | Visible |
| Other Windows | N/A | On-Demand | Auto-Close |

## Key Features

1. **Single Window Focus**
   - Only one main operational window visible at startup (Login)
   - Main window appears only after successful authentication

2. **Session Management**
   - Automatic session timeout checks
   - Secure session token handling
   - IP-based session tracking

3. **Window Transitions**
   - Smooth transitions between windows
   - Proper cleanup on window changes
   - State preservation during session

4. **Security**
   - Role-based access control
   - Permission checks on all operations
   - Activity logging
   - Session timeout handling

## Error Handling

```mermaid
graph TD
    A[Error Occurs] --> B[Log Error]
    B --> C{Critical?}
    C -->|Yes| D[Show Error Dialog]
    C -->|No| E[Log Warning]
    D --> F[Handle Recovery]
    E --> G[Continue Operation]
```

## Notes

1. **Window Management**
   - All windows inherit from QMainWindow
   - Consistent dark theme across windows
   - Centralized error handling

2. **Session Handling**
   - 60-minute session timeout
   - Automatic session validation
   - Secure token management

3. **User Experience**
   - Intuitive window transitions
   - Clear error messages
   - Consistent UI/UX 