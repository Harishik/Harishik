# Profile refresh

The proposed destination is the public profile repository `Harishik/Harishik`.
The workflow runs there on the default branch, roughly every six hours, or when manually dispatched.
It updates the README, still edition, public snapshot and rendered images.
Public pins are read from GitHub GraphQL, and the public contribution grid is read from GitHub’s logged-out calendar.
The workflow’s token writes only to the profile repository.
Repository metadata and the five configured media paths are read from the featured repositories.
GitHub continues to manage the profile’s native pin cards and contribution graph.

The featured project list and the media paths are defined in `tools/refresh_profile.py`.
The role line, profile links and paper list are editorial choices and can be edited there.
Name, public bio, avatar, pin order, featured metadata, configured images and the calendar can refresh.
If a featured file goes away, its README link can remain visible while the reel points readers to the project documentation.
The snapshot uses public contribution visibility as shown on GitHub and may include anonymized counts if the account exposes them.

GitHub Actions may delay scheduled runs or disable them after prolonged repository inactivity. The workflow never force-pushes.
