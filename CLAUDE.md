If I say:

FEATURE: I would like to ... (description goes here)

I would like you to:
1. check if I have uncommitted changes in git and warn me if I do.
2. if everything is checked in, create an appropriately named branch, based on the
feature description
3. interactively implement the future as you would normally do

I can then test it and we can interactively try to fix any issues.

If I say:

COMMIT

I want you to commit the changes to that branch, merge the branch into main, and delete that feature branch

If I say:

ROLLBACK

I want you to rollback all the changes made on that branch.