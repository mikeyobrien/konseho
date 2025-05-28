# GitHub Issue Prioritization

## Priority Levels

### P1 - CRITICAL Security Issues (Fix Immediately)
These vulnerabilities could lead to system compromise and must be addressed before any production use.

- **#21 Command Injection in shell_ops.py** - ✅ FIXED - Implemented command whitelist and proper validation
- **#22 Path Traversal in file_ops.py** - Allows reading/writing outside intended directories  
- **#23 API Keys Exposed in Logs** - Sensitive credentials visible in output

**Action**: Create a security-fixes branch and address these immediately with proper input validation and sanitization.

**Progress**: 
- #21 Fixed on refactor/dependency-injection branch - Added command whitelist, removed shell=True usage, implemented proper quote handling

### P2 - Production Stability Issues (Fix Before Production)
These issues can cause crashes, data loss, or resource exhaustion in production.

- **#1 Race Condition in EventEmitter** - Tasks not properly tracked, can cause lost events
- **#4 Thread Safety in ParallelExecutor** - Shared cache without locks in async context
- **#5 Resource Leak in MCP Manager** - MCP clients not cleaned up, will exhaust resources
- **#8 Memory Leak in Context History** - Unbounded growth will cause OOM errors

**Action**: Address after security fixes. Focus on proper async patterns and resource management.

### P3 - Core Missing Functionality (Required for MVP)
These features are documented but not implemented, breaking user expectations.

- **#24 MCP Tool Discovery** - Currently returns mock data instead of real tools
- **#26 Context Window Overflow** - No handling when context exceeds model limits
- **#27 Streaming Execution** - Stub implementation, needed for real-time responses
- **#29 Error Recovery Strategies** - Only basic retry implemented, no fallback options

**Action**: Implement after stability fixes. These are needed for a functional system.

### P4 - Architecture Refactoring (Current Sprint)
Already in progress on the refactor/dependency-injection branch.

- **#54 Extract Voting Logic** - Move from DebateStep to dedicated component
- **#55 Remove Test Mock Knowledge** - Production code shouldn't know about test mocks
- **#57 Simplify OutputManager** - Too much knowledge of data structures
- **#58 Decouple MCP Integration** - Make MCP optional/pluggable
- **#59 Simplify Step Hierarchy** - Reduce complexity in step classes
- **#60 Module Boundaries** - Create clear separation between modules

**Action**: Continue current refactoring work following SOLID principles.

### P5 - Testing Infrastructure (Quality Gates)
Essential for maintaining code quality and preventing regressions.

- **#25 Missing Test Coverage** - Critical components lack tests
- **#50 Poor Testing Infrastructure** - Need better test utilities and fixtures

**Action**: Add tests as part of each fix above. Create test utilities as needed.

### P6 - Error Handling & Reliability (Production Readiness)
Important for production resilience but not blocking.

- **#6 Inconsistent Retry Logic** - Error handling varies across components
- **#11 Async Context Issues** - Improper event loop handling
- **#28 No Rate Limiting** - Could overwhelm APIs
- **#38 Circuit Breaker Pattern** - Need fault tolerance for external services

**Action**: Implement after core functionality is stable.

### P7 - Design Patterns & Architecture (Future Enhancement)
Nice-to-have patterns that improve maintainability and extensibility.

- **#32 Dependency Injection Container** - For better testing and configuration
- **#33 State Machine for Workflow** - Formalize council execution states
- **#42 Strategy Pattern** - For configurable behaviors
- **#43 Builder Pattern** - For complex object construction

**Action**: Consider during major version updates or when extending functionality.

### P8 - Monitoring & Observability (Operations)
Needed for production operations but not blocking initial release.

- **#36 Metrics Collection** - No framework for performance metrics
- **#46 Health Check System** - No way to monitor system health
- **#48 Audit Trail** - Missing comprehensive logging

**Action**: Implement before production deployment or as operational needs arise.

## Recommended Execution Order

1. **Immediate**: Create hotfix branch for P1 security issues (#21, #22, #23)
2. **Next Sprint**: Address P2 stability issues (#1, #4, #5, #8) 
3. **Following Sprint**: Implement P3 core features (#24, #26, #27, #29)
4. **Ongoing**: Continue P4 refactoring work on current branch
5. **With Each Fix**: Add P5 test coverage
6. **Before Production**: Complete P6 reliability features
7. **Future Releases**: Consider P7 and P8 enhancements

## Quick Wins
Some issues can be fixed quickly and provide immediate value:
- **#16 Timezone-Naive Datetime** - Simple fix using timezone-aware datetimes
- **#17 O(n²) Vote Counting** - Easy algorithm optimization
- **#14 UTF-8 String Truncation** - Add proper boundary checking
- **#13 Missing Error Context** - Add context to error messages

## Dependencies
- Security fixes (P1) should be done before any other work
- Refactoring (P4) will make other fixes easier, so continue in parallel
- Testing infrastructure (P5) is needed to verify all other fixes