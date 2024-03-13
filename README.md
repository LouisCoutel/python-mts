## About
This is a custom client for Mapbox's services, adapted in part from their CLI tool **Mapbox Tilesets-CLI** (https://github.com/mapbox/tilesets-cli).
It aims to be a **complete toolbox** for interacting with most **Mapbox APIs** directly from a Python back end.

I wanted to manage maps and tilesets on the server in a fully automated way, and although Mapbox GL JS seemed like a pretty great tool, it's built to run client side and, well, it's Javascript and I was working with scientific data in Python. The other option was to use Mapbox Tilesets CLI, but that meant opening shells that actually run Python code from a Python server, which is pretty needlessly convoluted (and potentially not secure).

I did not consider myself proficient enough at that stage to build a client from the ground up, so I used the CLI tool as a blueprint. There were also quite a few quirks that would have been tricky to figure out just from reading the documentation, and this allowed me to get familiar with Mapbox's APIs and Python much faster.

As I progressed, I realized that this could very much turn into a fully fledged Python client, and I have started integrating endpoints from the **Styles API** as well.

## Disclaimer
I am aware that *maybe* this should be a fork of Tilesets-CLI. I started this on a whim and I had no idea if I would ever use it, let alone that I would still be working on it 3 months down the road.
**I intend to reach out to the contributors of Tilesets-CLI**, I simply did not find the time and to be frank I am still pretty clueless about how to approach them, having never contributed to open source or forked any large project.
