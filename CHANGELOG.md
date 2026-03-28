# [1.4.0](https://github.com/CtrI-Alt-Del/animus-server/compare/v1.3.0...v1.4.0) (2026-03-26)


### Bug Fixes

* ANI-57 address otp review feedback ([99d227f](https://github.com/CtrI-Alt-Del/animus-server/commit/99d227f7d58dcfc8aeb7b2af1c9d8281f799736b))
* ANI-57 enforce optional repository lookups and otp attempt limits ([8d0e30b](https://github.com/CtrI-Alt-Del/animus-server/commit/8d0e30b5727c6a255bad7e3b36fd65bb58b22fb9))
* ANI-57 reset verification attempts when generating otp ([d68c832](https://github.com/CtrI-Alt-Del/animus-server/commit/d68c8325383736733ee680472891da35c25f1e73))


### Features

* ANI-57 add auth seeding flow with faker support ([4a69c62](https://github.com/CtrI-Alt-Del/animus-server/commit/4a69c628918b1f4fb915017a64282c6129a8596a))
* ANI-57 add Dockerfile for multi-stage build with uvicorn setup ([756aafe](https://github.com/CtrI-Alt-Del/animus-server/commit/756aafe6f731d0c7340ac7a6d7ef4798da9168f6))
* ANI-57 implement otp email verification flow ([6cfa3c3](https://github.com/CtrI-Alt-Del/animus-server/commit/6cfa3c36656011353e181764d7d81776158370bc))

# [1.3.0](https://github.com/CtrI-Alt-Del/animus-server/compare/v1.2.0...v1.3.0) (2026-03-25)


### Bug Fixes

* ANI-34 resolve PR review findings on naming and docs ([32f8d87](https://github.com/CtrI-Alt-Del/animus-server/commit/32f8d87f30a96923553a85dd19b0e9874e20c586))


### Features

* **auth:** ANI-34 add email/password sign-in endpoint and domain errors ([eb7035c](https://github.com/CtrI-Alt-Del/animus-server/commit/eb7035cccdf9edc0401a9798d2e0255c0e56a9bd))

# [1.2.0](https://github.com/CtrI-Alt-Del/animus-server/compare/v1.1.0...v1.2.0) (2026-03-24)


### Features

* **auth:** #ANI-37 add sign in with google oauth ([aadbc4a](https://github.com/CtrI-Alt-Del/animus-server/commit/aadbc4a9906f44acc02310bb5ea75591e5210af6)), closes [#ANI-37](https://github.com/CtrI-Alt-Del/animus-server/issues/ANI-37)

# [1.1.0](https://github.com/CtrI-Alt-Del/animus-server/compare/v1.0.0...v1.1.0) (2026-03-23)


### Features

* **docs:** #ANI-56 add swagger docs ([f7cea7d](https://github.com/CtrI-Alt-Del/animus-server/commit/f7cea7d153f2086735a89c231f259bc4e00185ba)), closes [#ANI-56](https://github.com/CtrI-Alt-Del/animus-server/issues/ANI-56)

# 1.0.0 (2026-03-23)


### Bug Fixes

* ANI-21 resolve PR review feedback across core, docs, and tooling ([3d26712](https://github.com/CtrI-Alt-Del/animus-server/commit/3d26712095ff5325c6972d25ad0f52f555aad561))
* ANI-25 update PostgreSQL port mapping in docker-compose.yaml ([6027092](https://github.com/CtrI-Alt-Del/animus-server/commit/6027092345d2bcd2c03986e28bdc6e5cf786c5ec))


### Features

* ANI-21 bootstrap animus server structure and documentation ([b3c326e](https://github.com/CtrI-Alt-Del/animus-server/commit/b3c326e065e1099ff6aca65604096ef6be6342da))
* **auth:** ANI-35 implement sign-up workflow with persistence and email verification ([96b3516](https://github.com/CtrI-Alt-Del/animus-server/commit/96b35163f8f62fe623f65193f3937e9404677a0f))
* **auth:** ANI-52 add auth domain entities structures and interfaces ([60fbbab](https://github.com/CtrI-Alt-Del/animus-server/commit/60fbbab3a562bf96982025bd809b838ed700edcd))
* **intake:** ANI-52 add intake domain entities structures and interfaces ([a01b9f8](https://github.com/CtrI-Alt-Del/animus-server/commit/a01b9f813631aa137c5dac02b76e9d5e4aae5121))
* **storage:** ANI-52 add storage structures and provider interfaces ([473cf57](https://github.com/CtrI-Alt-Del/animus-server/commit/473cf57fab00bdaea205fc25b6364e74eff236a5))
