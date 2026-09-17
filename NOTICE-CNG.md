# RustDesk CNG server — modified distribution

Modification date: 2026-09-16.

This is a modified RustDesk server, not an official upstream release.
Original copyright and attribution notices, including those of Purslane Ltd.
and other contributors, are retained. This modified work is distributed
under GNU Affero General Public License version 3; see LICENSE. You may
redistribute and modify it under that license. It is provided WITHOUT ANY
WARRANTY, including merchantability or fitness for a particular purpose,
except where separately agreed in writing. Dependency licenses remain
applicable to their respective code.

The application starts from rustdesk-server revision
f6cb7556d5761a4530493ab68a744183898ed386 with local modifications.
The local hbb_common comes from rustdesk/rustdesk-server revision
772db7422f679db1fa06be1097cd676a73055851, before its extraction.
The historical client encryption/key-exchange support comes from
rustdesk/rustdesk revision 4b066b1fbaa8d5d6f9b53cb1e5b25e484f229da1.
Changes include certificate authentication of technicians, authenticated
encrypted TCP ports, relay authorization, historical library integration
and removal of the newer automatic update check.

Operators must prominently offer every user interacting remotely with this
modified software access to its corresponding source at no charge, as
required by AGPL section 13. The download site's source offer must identify
the actual server version deployed, as well as the client version.
The public source distribution must not contain production private keys,
technician private keys, user databases or deployment credentials.
