# Installation

Installation instructions for hurl at https://hurl.dev/docs/installation.htm

Note that you do not need hurl to run the app locally but it does form part of
the post-deploy checks so it useful to install locally.

# Invocation

Run these tests as:

```shell

hurl --test -m 10  --variable host=http://localhost:3000 *.hurl
```

The `-m` switch is a timeout so that the tests will fail in a sensible time in
the event of the app not being available.

The `--test` switch stops the page content from being shown and gives a useful
test-orientated summary at the end.

Replace the `host` variable with a suitable prefix based on how you're running
the app (in the case of local development) or which environment you wish to
test (in the case of a hosted environment).

# More information

See the main hurl website at https://hurl.dev/
