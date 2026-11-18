<!-- SPDX-License-Identifier: Apache-2.0 -->
# Rust `std` on NeoSymbian (browser WB2)

Written 2026-11-17. This is the working doc for [browser.md](browser.md) stage **WB2**: Rust's standard library for
NeoSymbian, which Servo, SpiderMonkey's Rust side, Tokio and rustls all need. Today all our Rust is `no_std`.

**WB2's gate** (browser.md):
- Rust's std tests on the emulator and the phone;
- one EXE mixing `std`, e32 and C++;
- a Tokio TCP fetch over NeoNet.

## Steps

| Step | What | State |
|---|---|---|
| **WB2a** | ARMv7 + NEON user code with the soft-float calling convention: e32-rs `targets/armv7a-neosymbian-eabi.json`, `cargo arm7` | ✅ 2026-11-17 (e32-rs#4): neotest 10/10, NEOWB1 6/6 on QEMU and the Pixel |
| **WB2b** | Rust EXEs import from P.I.P.S.'s DLLs (build `exes.txt` `libs=`); `PIPSPROB.EXE` measures P.I.P.S. | ✅ 2026-11-18 on QEMU and the Pixel (identical results) |
| **WB2c-1** | P.I.P.S. fixed in our forks: `clock_gettime` nanoseconds, `CLOCK_MONOTONIC` (generic timer, kernel EL0VCTEN), new `poll`/`pread`/`pwrite` exports; libc built without GCC builtins | ✅ 2026-11-18 on QEMU and the Pixel: PIPSPROB 19 ok, 0 failed (kernel#21, ossrv#1, legacy#6) |
| **WB2c-2** | Forks on branch `neosymbian`: `NeoSymbian/libc` (`src/unix/symbian`) and `NeoSymbian/rust` `library/` only (on `nightly-2026-10-20` = 07e526db9, the toolchain e32-rs pins): `target_os = "symbian"` in the unix family; e32's std mode | ✅ 2026-11-18 on QEMU and the Pixel: STDTEST 17 ok, 1 skipped (no IP stack); MIXTEST all ok (browser#4, e32-rs#5, build#33) |
| **WB2d** | `NeoSymbian/mio` (the `poll` selector over our `poll`), Tokio `current_thread`; an HTTP fetch over NeoNet on the phone | in progress: Tokio runs, DNS works over Wi-Fi; TCP through P.I.P.S. stalls (browser#5 draft, kernel#23, build#34) |

## Why forks

Rust's standard library and the crates under it build only for operating systems they already list, and
`target_os = "symbian"` is on none of those lists. The change has to live somewhere until upstream takes it: forks of
**rust**, **libc** and **mio** on branch `neosymbian` (the workspace fork rule), with the nightly pinned so nothing
moves under us.

| Fork | What we add | Why it can't be avoided |
|---|---|---|
| `NeoSymbian/rust` (`library/` only; the compiler is the stock pinned nightly) | `symbian` in std's per-OS choices: the thread, file, time and random code to use; no process spawning; the WB2b workarounds (monotonic time from the kernel counter, `poll` over `select`, our timed waits) | std does not build for an unknown OS, and P.I.P.S.'s gaps need Symbian code inside it |
| `NeoSymbian/libc` | P.I.P.S.'s exact sizes and constants (PIPSPROB: `AF_INET6` = 2054, 32-bit `time_t`, 96-byte `stat`, ...) | Rust calls C through these; a wrong value corrupts memory |
| `NeoSymbian/mio` | `symbian` on mio's `poll()` backend list | Tokio sits on mio, which does not compile for an unknown OS |

Each change is small: cfg lines, plus one new module in libc and one OS folder in std. WB2d added **socket2** and
**tokio** forks for the same reason: each lists the OSes it knows (Symbian follows vita in both). Skipping `std` is not an option,
since Servo and its ~500 dependencies all assume it.

**Later: back to upstream** (on the [roadmap](roadmap.md)). The forks are the start, not the end state:
- re-sync them on every nightly bump;
- offer the libc module and the mio cfgs upstream once they are stable;
- then propose `armv7a-symbian-eabi` as a **tier 3** Rust target, as NuttX, Vita and the 3DS (`horizon`) did. That
  needs named target maintainers.

Once upstream takes them, the forks shrink to nothing.

## Building for it

- **Target:** `armv7a-neosymbian-eabi`, which is:
  - ARMv7-A/ARMv8-AArch32, VFPv3-D32 + NEON;
  - the soft-float calling convention, so calls into the 2010 libraries stay compatible;
  - 64-bit atomics.
- **`+no-movt` (GCC: `-mword-relocations`) is required.** E32 images relocate whole 32-bit words only, so a
  MOVW/MOVT address pair (relocs 43/44) cannot be loaded. The EXE writer refuses it ("reloc type 43 unsupported").
- **A Rust EXE that calls C libraries** lists them in its `exes.txt` line, as an mmp's LIBRARY:

  ```
  PIPSPROB.EXE   0xE0007002  libpipsprobe.a     rust/pipsprobe.cpp  libs=libc,libpthread,libm
  ```

  Imports resolve by ordinal from the components' frozen `.def` files (`build_mmp.provider_maps`). A glue `.cpp`
  then also sees P.I.P.S.'s headers (`stdapis`, `-D__SOFTFP=`). Function imports only; a DATA import fails clearly.
- **P.I.P.S. needs a cleanup stack** in each thread that calls it. Without one, `opendir` panics with
  E32USER-CBase 69. A C program's crt0 creates it, an `e32::main!` EXE does not; std's start-up must
  (`CTrapCleanup::New()`).

## What PIPSPROB.EXE found (QEMU virt and the Pixel, WB1 kernel, the eshell ROM; 2026-11-18)

`PIPSPROB.EXE` (`NeoSymbian/browser` `symbian/pipsprobe`) runs a C check per behaviour std needs and prints every
size, field offset and constant the Rust `libc` port needs. These tables come from its serial output through
`browser/tools/pips_layout.py`.

**Summary:** 14 ok, 2 failed, 8 not supported, on QEMU and on the phone alike.

### Gaps and what the port does about them

| Gap | Effect | WB2c answer |
|---|---|---|
| `pthread_cond_timedwait` returns ETIMEDOUT at once | timed waits (`Condvar::wait_timeout`, `park_timeout`, channels with timeouts) would spin | **Fixed in the ossrv fork**: the cause was `clock_gettime(CLOCK_REALTIME)` putting the whole microsecond count since year 0 in `tv_nsec`, so every deadline was garbage |
| `clock_gettime(CLOCK_MONOTONIC)` → EINVAL (the constant exists, = 4) | no `Instant` | **Added in the ossrv fork**: the ARM generic timer's 64-bit count (CNTVCT at CNTFRQ), which the kernel now lets EL0 read (CNTKCTL_EL1.EL0VCTEN). Only on the SMP (AArch64) kernel; Syborg's Cortex-A8 keeps EINVAL |
| no `pthread_condattr_setclock` | — | condvar on CLOCK_REALTIME (as espidf/horizon) |
| no `poll()` (`struct pollfd` only); `select()` exists, `FD_SETSIZE` 1024 | std's `init` and connect timeouts; mio | **Added to libc.dll** (ordinal 598): `poll()` over `select()`; std skips its init `poll` (as vita/horizon) |
| no `pread`/`pwrite` | `FileExt::read_at`/`write_at` | **Added to libc.dll** (599, 600): lseek + read/write, not atomic against another user of the fd |
| no `posix_memalign` | the allocator's large alignments | std's `System` aligns over `malloc` (over-allocate + offset) |
| no `MAP_ANON`; file `mmap` → errno 24 | — | not used by std; SpiderMonkey's GC uses EKA2 chunks (WB1) |
| no `O_CLOEXEC`, `SOCK_CLOEXEC`, `SOCK_NONBLOCK`, `F_DUPFD_CLOEXEC`, `O_DIRECTORY` | std's cloexec paths | flags 0 / the `fcntl` fallbacks (no exec on Symbian anyway) |
| `pipe()` and `socket()` → ENOENT | — | the eshell ROM starts no IP stack: re-test in the UI ROM (NeoNet's ESOCK, WB2d) |
| cwd is `Z:\Private\<SID>` (read-only) | relative paths | left as is: std keeps P.I.P.S.'s cwd, apps use absolute `C:/...` paths |

### Key facts for the `libc` port

- **ILP32:** `long` 4 bytes, `size_t` 4.
- **Integer types:**
  - `off_t` **8**;
  - `time_t` **4**;
  - `mode_t` **2**;
  - `ino_t` 4;
  - `dev_t` 4;
  - `wchar_t` 2 (`-fshort-wchar`).
- **Structs:**
  - `struct stat` 96 bytes, `st_size` at 48;
  - `struct dirent` 264;
  - `sockaddr_in` 28;
  - `addrinfo` 32.
- **pthread types:** `pthread_t` 4, `pthread_mutex_t` 12, `pthread_cond_t` 24, `pthread_key_t` 4.
- **Mutex types:** NORMAL 0, RECURSIVE 1, ERRORCHECK 2 (enum values).
- **errno (BSD values):** EAGAIN 35, ETIMEDOUT 60.
- **Socket and file constants:** AF_INET6 is **2054** (Symbian's value, not BSD's 28); O_NONBLOCK 4.

### The checks

| Check | Result | Detail |
|---|---|---|
| `thread_join` | ok | joined, result 42 |
| `thread_stack_8m` | ok | 8 MiB stack used to 7 MiB |
| `thread_detach_self` | ok | detach ok, self 11535448 |
| `tls_key` | ok | per-thread values 3 and 7 |
| `mutex` | ok | recursive x3, static initializer |
| `condvar` | ok | signalled |
| `condvar_timedwait` | FAILED | returned 60 after 0 ms (want ETIMEDOUT after ~100) |
| `condattr_setclock` | NOTSUP | pthread_condattr_setclock not in P.I.P.S.: std's condvar uses CLOCK_REALTIME |
| `clocks` | FAILED | MONOTONIC errno 22 |
| `sched_yield` | ok | ok |
| `file_rw` | ok | open/write/lseek/read/fstat/ftruncate/fsync/stat/rename/unlink, ENOENT |
| `dir_ops` | ok | mkdir/opendir/readdir (1 entries)/rmdir |
| `cwd` | ok | cwd 'Z:\Private\e0007002', realpath(.) 'Z:\Private\e0007002' |
| `env` | ok | set/get/unset |
| `memory` | NOTSUP | page 4096, malloc/realloc ok; mmap(file) errno 24; no MAP_ANON |
| `pipe_select` | NOTSUP | pipe errno 2 |
| `poll` | NOTSUP | poll() not in P.I.P.S. (struct pollfd only); select() is: poll over select |
| `pread` | NOTSUP | pread/pwrite not in P.I.P.S.: FileExt::read_at via lseek+read |
| `posix_memalign` | NOTSUP | posix_memalign not in P.I.P.S.: std's allocator aligns over malloc |
| `errno_values` | ok | missing file -> errno 2 (ENOENT 2), ENOTDIR 20 |
| `getpid` | ok | pid 39 |
| `tcp_loopback` | NOTSUP | socket errno 2 |
| `udp_loopback` | NOTSUP | socket errno 2 |
| `getaddrinfo_local` | ok | numeric host resolved, port 80 |

### All layout values

| Name | Value |
|---|---:|
| `sizeof(long)` | 4 |
| `sizeof(size_t)` | 4 |
| `sizeof(ssize_t)` | 4 |
| `sizeof(off_t)` | 8 |
| `sizeof(time_t)` | 4 |
| `sizeof(clock_t)` | 4 |
| `sizeof(pid_t)` | 4 |
| `sizeof(uid_t)` | 4 |
| `sizeof(gid_t)` | 4 |
| `sizeof(mode_t)` | 2 |
| `sizeof(dev_t)` | 4 |
| `sizeof(ino_t)` | 4 |
| `sizeof(nlink_t)` | 2 |
| `sizeof(blksize_t)` | 4 |
| `sizeof(blkcnt_t)` | 8 |
| `sizeof(socklen_t)` | 4 |
| `sizeof(sa_family_t)` | 1 |
| `sizeof(in_port_t)` | 2 |
| `sizeof(in_addr_t)` | 4 |
| `sizeof(nfds_t)` | 4 |
| `sizeof(wchar_t)` | 2 |
| `sizeof(pthread_t)` | 4 |
| `sizeof(pthread_attr_t)` | 32 |
| `sizeof(pthread_mutex_t)` | 12 |
| `sizeof(pthread_mutexattr_t)` | 12 |
| `sizeof(pthread_cond_t)` | 24 |
| `sizeof(pthread_condattr_t)` | 4 |
| `sizeof(pthread_key_t)` | 4 |
| `sizeof(pthread_once_t)` | 4 |
| `sizeof(fd_set)` | 128 |
| `sizeof(struct stat)` | 96 |
| `stat.st_dev` | 0 |
| `sizeof(stat.st_dev)` | 4 |
| `stat.st_ino` | 4 |
| `sizeof(stat.st_ino)` | 4 |
| `stat.st_mode` | 8 |
| `sizeof(stat.st_mode)` | 2 |
| `stat.st_nlink` | 10 |
| `sizeof(stat.st_nlink)` | 2 |
| `stat.st_uid` | 12 |
| `sizeof(stat.st_uid)` | 4 |
| `stat.st_gid` | 16 |
| `sizeof(stat.st_gid)` | 4 |
| `stat.st_rdev` | 20 |
| `sizeof(stat.st_rdev)` | 4 |
| `stat.st_size` | 48 |
| `sizeof(stat.st_size)` | 8 |
| `stat.st_atime` | 24 |
| `sizeof(stat.st_atime)` | 4 |
| `stat.st_mtime` | 32 |
| `sizeof(stat.st_mtime)` | 4 |
| `stat.st_ctime` | 40 |
| `sizeof(stat.st_ctime)` | 4 |
| `stat.st_blksize` | 64 |
| `sizeof(stat.st_blksize)` | 4 |
| `stat.st_blocks` | 56 |
| `sizeof(stat.st_blocks)` | 8 |
| `sizeof(struct dirent)` | 264 |
| `dirent.d_ino` | 0 |
| `sizeof(dirent.d_ino)` | 4 |
| `dirent.d_name` | 8 |
| `sizeof(dirent.d_name)` | 256 |
| `sizeof(struct timespec)` | 8 |
| `timespec.tv_sec` | 0 |
| `sizeof(timespec.tv_sec)` | 4 |
| `timespec.tv_nsec` | 4 |
| `sizeof(timespec.tv_nsec)` | 4 |
| `sizeof(struct timeval)` | 8 |
| `timeval.tv_sec` | 0 |
| `sizeof(timeval.tv_sec)` | 4 |
| `timeval.tv_usec` | 4 |
| `sizeof(timeval.tv_usec)` | 4 |
| `sizeof(struct sockaddr)` | 30 |
| `sockaddr.sa_family` | 0 |
| `sizeof(sockaddr.sa_family)` | 2 |
| `sockaddr.sa_data` | 4 |
| `sizeof(sockaddr.sa_data)` | 24 |
| `sizeof(struct sockaddr_in)` | 28 |
| `sockaddr_in.sin_family` | 0 |
| `sizeof(sockaddr_in.sin_family)` | 2 |
| `sockaddr_in.sin_port` | 2 |
| `sizeof(sockaddr_in.sin_port)` | 2 |
| `sockaddr_in.sin_addr` | 4 |
| `sizeof(sockaddr_in.sin_addr)` | 4 |
| `sockaddr_in.sin_zero` | 8 |
| `sizeof(sockaddr_in.sin_zero)` | 20 |
| `sizeof(struct sockaddr_in6)` | 32 |
| `sockaddr_in6.sin6_family` | 0 |
| `sizeof(sockaddr_in6.sin6_family)` | 2 |
| `sockaddr_in6.sin6_port` | 2 |
| `sizeof(sockaddr_in6.sin6_port)` | 2 |
| `sockaddr_in6.sin6_flowinfo` | 20 |
| `sizeof(sockaddr_in6.sin6_flowinfo)` | 4 |
| `sockaddr_in6.sin6_addr` | 4 |
| `sizeof(sockaddr_in6.sin6_addr)` | 16 |
| `sockaddr_in6.sin6_scope_id` | 24 |
| `sizeof(sockaddr_in6.sin6_scope_id)` | 4 |
| `sizeof(struct sockaddr_storage)` | 128 |
| `sizeof(struct addrinfo)` | 32 |
| `addrinfo.ai_flags` | 0 |
| `sizeof(addrinfo.ai_flags)` | 4 |
| `addrinfo.ai_family` | 4 |
| `sizeof(addrinfo.ai_family)` | 4 |
| `addrinfo.ai_socktype` | 8 |
| `sizeof(addrinfo.ai_socktype)` | 4 |
| `addrinfo.ai_protocol` | 12 |
| `sizeof(addrinfo.ai_protocol)` | 4 |
| `addrinfo.ai_addrlen` | 16 |
| `sizeof(addrinfo.ai_addrlen)` | 4 |
| `addrinfo.ai_canonname` | 20 |
| `sizeof(addrinfo.ai_canonname)` | 4 |
| `addrinfo.ai_addr` | 24 |
| `sizeof(addrinfo.ai_addr)` | 4 |
| `addrinfo.ai_next` | 28 |
| `sizeof(addrinfo.ai_next)` | 4 |
| `sizeof(struct pollfd)` | 8 |
| `pollfd.fd` | 0 |
| `sizeof(pollfd.fd)` | 4 |
| `pollfd.events` | 4 |
| `sizeof(pollfd.events)` | 2 |
| `pollfd.revents` | 6 |
| `sizeof(pollfd.revents)` | 2 |
| `sizeof(struct linger)` | 8 |
| `linger.l_onoff` | 0 |
| `sizeof(linger.l_onoff)` | 4 |
| `linger.l_linger` | 4 |
| `sizeof(linger.l_linger)` | 4 |
| `sizeof(struct iovec)` | 8 |
| `iovec.iov_base` | 0 |
| `sizeof(iovec.iov_base)` | 4 |
| `iovec.iov_len` | 4 |
| `sizeof(iovec.iov_len)` | 4 |
| `PTHREAD_MUTEX_NORMAL` | 0 |
| `PTHREAD_MUTEX_RECURSIVE` | 1 |
| `PTHREAD_MUTEX_DEFAULT` | 0 |
| `PTHREAD_MUTEX_ERRORCHECK` | 2 |
| `PTHREAD_CREATE_JOINABLE` | 0 |
| `PTHREAD_CREATE_DETACHED` | 1 |
| `EPERM` | 1 |
| `ENOENT` | 2 |
| `EINTR` | 4 |
| `EIO` | 5 |
| `EBADF` | 9 |
| `EAGAIN` | 35 |
| `EWOULDBLOCK` | 35 |
| `ENOMEM` | 12 |
| `EACCES` | 13 |
| `EEXIST` | 17 |
| `ENOTDIR` | 20 |
| `EISDIR` | 21 |
| `EINVAL` | 22 |
| `ENFILE` | 23 |
| `EMFILE` | 24 |
| `ENOSPC` | 28 |
| `ESPIPE` | 29 |
| `EROFS` | 30 |
| `EPIPE` | 32 |
| `ERANGE` | 34 |
| `EDEADLK` | 11 |
| `ENAMETOOLONG` | 63 |
| `ENOSYS` | 78 |
| `ENOTEMPTY` | 66 |
| `ELOOP` | 62 |
| `EINPROGRESS` | 36 |
| `EALREADY` | 37 |
| `ENOTSOCK` | 38 |
| `EMSGSIZE` | 40 |
| `EPROTONOSUPPORT` | 43 |
| `EOPNOTSUPP` | 45 |
| `ENOTSUP` | 45 |
| `EAFNOSUPPORT` | 47 |
| `EADDRINUSE` | 48 |
| `EADDRNOTAVAIL` | 49 |
| `ENETDOWN` | 50 |
| `ENETUNREACH` | 51 |
| `ECONNABORTED` | 53 |
| `ECONNRESET` | 54 |
| `ENOBUFS` | 55 |
| `EISCONN` | 56 |
| `ENOTCONN` | 57 |
| `ETIMEDOUT` | 60 |
| `ECONNREFUSED` | 61 |
| `EHOSTUNREACH` | 65 |
| `EXDEV` | 18 |
| `EBUSY` | 16 |
| `EFBIG` | 27 |
| `EMLINK` | 31 |
| `ETXTBSY` | 26 |
| `O_RDONLY` | 0 |
| `O_WRONLY` | 1 |
| `O_RDWR` | 2 |
| `O_ACCMODE` | 3 |
| `O_CREAT` | 512 |
| `O_EXCL` | 2048 |
| `O_TRUNC` | 1024 |
| `O_APPEND` | 8 |
| `O_NONBLOCK` | 4 |
| `O_CLOEXEC` | absent |
| `O_DIRECTORY` | absent |
| `O_NOFOLLOW` | 256 |
| `O_SYNC` | 128 |
| `F_DUPFD` | 0 |
| `F_DUPFD_CLOEXEC` | absent |
| `F_GETFD` | 1 |
| `F_SETFD` | 2 |
| `F_GETFL` | 3 |
| `F_SETFL` | 4 |
| `FD_CLOEXEC` | 1 |
| `FD_SETSIZE` | 1024 |
| `S_IFMT` | 61440 |
| `S_IFDIR` | 16384 |
| `S_IFREG` | 32768 |
| `S_IFLNK` | 40960 |
| `S_IFIFO` | 4096 |
| `S_IFSOCK` | 49152 |
| `S_IFCHR` | 8192 |
| `S_IFBLK` | 24576 |
| `SEEK_SET` | 0 |
| `SEEK_CUR` | 1 |
| `SEEK_END` | 2 |
| `AF_UNSPEC` | 0 |
| `AF_INET` | 2048 |
| `AF_INET6` | 2054 |
| `AF_UNIX` | 1 |
| `AF_LOCAL` | 1638 |
| `SOCK_STREAM` | 1 |
| `SOCK_DGRAM` | 2 |
| `SOCK_RAW` | 4 |
| `SOCK_CLOEXEC` | absent |
| `SOCK_NONBLOCK` | absent |
| `SOL_SOCKET` | 1 |
| `SO_REUSEADDR` | 1030 |
| `SO_ERROR` | 9 |
| `SO_TYPE` | 4104 |
| `SO_RCVTIMEO` | 4102 |
| `SO_SNDTIMEO` | 4101 |
| `SO_BROADCAST` | -1 |
| `SO_LINGER` | -3 |
| `SO_KEEPALIVE` | 773 |
| `SO_RCVBUF` | 2 |
| `SO_SNDBUF` | 3 |
| `IPPROTO_IP` | 256 |
| `IPPROTO_IPV6` | 41 |
| `IPPROTO_TCP` | 6 |
| `IPPROTO_UDP` | 17 |
| `TCP_NODELAY` | 1 |
| `IP_TTL` | 784 |
| `IPV6_V6ONLY` | 27 |
| `IP_MULTICAST_TTL` | -6 |
| `IP_MULTICAST_LOOP` | -7 |
| `IP_ADD_MEMBERSHIP` | 1133 |
| `IPV6_JOIN_GROUP` | 12 |
| `MSG_PEEK` | 2 |
| `MSG_DONTWAIT` | 128 |
| `MSG_NOSIGNAL` | 131072 |
| `MSG_WAITALL` | 64 |
| `SHUT_RD` | 0 |
| `SHUT_WR` | 1 |
| `SHUT_RDWR` | 2 |
| `POLLIN` | 1 |
| `POLLPRI` | 2 |
| `POLLOUT` | 4 |
| `POLLERR` | 8 |
| `POLLHUP` | 16 |
| `POLLNVAL` | 32 |
| `FIONBIO` | -2147195266 |
| `FIONREAD` | 1074030207 |
| `INADDR_ANY` | 0 |
| `INADDR_LOOPBACK` | 2130706433 |
| `AI_PASSIVE` | 1 |
| `AI_CANONNAME` | 2 |
| `AI_NUMERICHOST` | 4 |
| `EAI_AGAIN` | 2 |
| `EAI_FAIL` | 4 |
| `EAI_FAMILY` | 5 |
| `EAI_NONAME` | 8 |
| `EAI_SERVICE` | 9 |
| `EAI_SOCKTYPE` | 10 |
| `EAI_SYSTEM` | 11 |
| `CLOCK_REALTIME` | 0 |
| `CLOCK_MONOTONIC` | 4 |
| `PTHREAD_STACK_MIN` | 8192 |
| `_SC_PAGESIZE` | 47 |
| `_SC_NPROCESSORS_ONLN` | 58 |
| `PATH_MAX` | 256 |
| `PROT_NONE` | 0 |
| `PROT_READ` | 1 |
| `PROT_WRITE` | 2 |
| `MAP_PRIVATE` | 2 |
| `MAP_ANON` | absent |
| `MAP_ANONYMOUS` | absent |
| `MAP_FAILED` | -1 |
| `DT_DIR` | 4 |
| `DT_REG` | 8 |
| `DT_LNK` | 10 |
| `DT_UNKNOWN` | 0 |
| `STDIN_FILENO` | 0 |

## What WB2c found and did (2026-11-18)

**Results**, identical on QEMU virt and the Pixel 3a XL (WB1 kernel, eshell ROM):
- PIPSPROB: 19 ok, 0 failed (was 14 ok, 2 failed).
- STDTEST.EXE (browser `std/stdtest`): 17 ok, 0 failed, 1 skipped. Network is skipped because this ROM starts no IP
  stack; it is re-tested in WB2d.
- MIXTEST.EXE (`std/mixtest`): std threads call Symbian C++ (TRAP, `CArrayFixFlat`), which calls back into Rust;
  e32 runs alongside; 225 libc sizes, offsets and constants match P.I.P.S.'s own headers.

**Building:**
- `tools/neosymbian-toolchain.sh RUST_CHECKOUT [LIBC_CHECKOUT]` makes the `neosymbian` toolchain: the pinned nightly
  with the fork's `library/` as rust-src.
- Then, in browser `std/`, `cargo sym`.
- Cargo does not notice changes in build-std sources, so run `cargo clean` after changing the fork.
- `exes.txt` lines for a std EXE need `libs=libc,libpthread,libm` and `heap=` (build's new column).

**Findings:**
- **P.I.P.S.'s `libc.dll` was miscompiled.** GCC turned `memset.c`'s loops into `memset` calls and `calloc.c`'s
  malloc + bzero into a `calloc` call, so both recursed until the stack overflowed (KERN-EXEC 3). Every P.I.P.S.
  program that zero-allocates was affected. libc is now built with `-fno-builtin -fno-tree-loop-distribute-patterns`
  (legacy#6).
- **P.I.P.S.'s `__crt0` blocks** when its IPC server is not running: it first asks whether `popen`/`posix_spawn`
  started the process. std's start-up therefore does without it:
  - the cleanup stack;
  - `args` from `User::CommandLine` and `RProcess::FileName`;
  - `environ` through `__environ()`.
- **No unwinder.** Symbian EXEs are `panic=abort`, with no backtraces and no EH personality. libgcc's unwinder needs
  a C++ runtime Symbian does not export, so std defines aborting stubs for the `_Unwind_*` names it still mentions.
- **C enums are 32-bit** (the Symbian objects' EABI tag; `sizeof(enum)` = 4 in MIXTEST). The std target sets
  `c-enum-min-bits` 32. The no_std targets still say 8; nothing passes a `repr(C)` enum to Symbian today.
- **Paths:** use `C:/...`. std splits paths at `/` and P.I.P.S. accepts both separators; `/x` lands on the cwd's
  drive (Z:, read-only). `canonicalize` (realpath) returns EINVAL for `/` paths.
- **Sleep granularity** is the kernel tick: `sleep(0.5 ms)` takes ~15 ms.
- **stdout and stderr** go to the kernel debug port a line at a time, so panic messages reach the serial log.
- **The allocator** is P.I.P.S. `malloc` (RHeap, 8-aligned) on the EXE's own heap; larger alignments over-allocate.
- **`IPPROTO_IP` is 0x100 on Symbian.** The shared unix value (0) silently shadowed ours, and MIXTEST caught it.

**Not done:**
- `posix_memalign` (std over-allocates instead);
- `MAP_ANON` (WB3: SpiderMonkey uses chunks);
- `chdir` to `C:` at start-up;
- unwinding;
- process spawning (`posix_spawn` exists for later).

## WB2d so far (2026-11-18)

**Done:**
- **Pipes.** The kernel links Symbian's pipe LDD in (kernel#23, with `umemget`), and build's loader answers
  `LoadLogicalDevice("PIPELIB")` (build#34). PIPSPROB's `pipe_select` now passes: 20 ok, 0 failed.
- **Forks on branch `neosymbian`, as vita:**
  - `NeoSymbian/mio`: the `poll` selector and a `pipe()` waker;
  - `NeoSymbian/socket2`: as vita, but `fcntl(O_NONBLOCK)`;
  - `NeoSymbian/tokio`: no peer credentials.
  - libc gained the socket constants they use.
- **NETTEST.EXE** (browser `std/nettest`, browser#5 draft):
  - **Tokio's `current_thread` runtime works** on QEMU and the Pixel: timers, tasks, mpsc, timeouts, and
    `spawn_blocking` waking the runtime through the pipe waker.
  - **DNS works over Wi-Fi** through P.I.P.S. (`getaddrinfo`).

**Open: TCP through P.I.P.S.**
- On the phone (UI ROM, NeoNet up), a blocking `connect()` never completes.
- Tokio's non-blocking connect and `bind` fail with ENOSYS.
- NEOSOCK (the 2010 `RSocket` API) passed TCP on the phone in W5a, so the difference lies in P.I.P.S.'s socket path.
  Candidates:
  - its default connection and lazy `maybe_reopen_socket`;
  - `getsockopt(SO_ERROR)` (`KSOSelectLastError`) reaching NEONET.PRT's `GetOption`, which returns
    KErrNotSupported (P.I.P.S. maps that to ENOSYS);
  - `bind` on a TCP socket.
- NETTEST's `socket_diag` prints each raw step with its errno, for that investigation.
