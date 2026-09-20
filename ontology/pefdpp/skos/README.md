# EF 3.1 elementary flows — deliberately not committed

`ef31-elementaryflows.ttl` is the full EF 3.1 flow list: **41 MB**, against 328 KB for
every other ontology file here combined. It is excluded from version control.

## Why

The battery case study references elementary flows **by UUID** and never imports this
file, so nothing in the default path needs it. Parsing it adds roughly 40 seconds to
startup. Committing it would put 41 MB into every clone, every CI checkout and every
archived release, permanently, to serve a lookup that is optional.

The cost of leaving it out is one documented step for the few queries that want flow
labels rather than UUIDs. The cost of putting it in is paid by everyone, forever.

## Getting it

It ships with the PEFDPP ontology release. Place it at this path and
`PefdppGraphService.load_elementary_flow_scheme()` will pick it up; without it, that
method reports the file is absent rather than failing, and every other query works
unchanged.

## What depends on it

Only flow **labels**. Characterisation factors are joined by UUID from
`data/pefdpp/factors/ef31_characterisation_factors.json`, which is small and is
committed — so impact results are complete with or without this file.
