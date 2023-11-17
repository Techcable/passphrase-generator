# passphrase-generator
A small Python script to generate passphrases based on a given wordlist.

Uses the [`secrets`] module for cryptographically secure random number generation.

The only dependency outside the stdlib is [`click`].

## TODO
- [ ] Automatically detect wordlist format from file
- [ ] Simplify codebase??

[`secrets`]: https://docs.python.org/3/library/secrets.html
[`click`]: https://click.palletsprojects.com
