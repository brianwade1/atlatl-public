# S16 coverage and limits

Research probes run unchanged source in fresh 60-second subprocesses, with a
fixed hash seed and disposable tests-local cwd. Torch probes use CPU, seed 1729
and one thread. Missing dependencies fail rather than skip.

| Items | Coverage |
| --- | --- |
| 1 | `ml/test_portabletorch.py`: real fixture persistence, metadata/source/dependency copy, CPU map-location, eval, weights/predictions, distinct loaded classes, same-file copy, print/test and six invalid artifact cases. |
| 2-3 | `ml/test_network_shapes.py`: all five CNNs, simple Model, dataset dtype/indexing, residual oracle, finite shapes, repeated small construction; four train helpers first fail without device, then run one CPU batch with SGD, finite losses/gradients and changed parameters. dlalphabeta has no train helper. |
| 4-5 | `ml/test_alphazero_game.py`: controlled real 5x5 registry, pass/masks/delegation, empty/off-map origins, 24 direction/parity/move/fire round trips, canonical cities/factions/score and input preservation, raw score, wider-action characterization, one symmetry, 16-channel features, phase/score, stale parameter versus current-state placement, red score characterization. |
| 6 | `ml/test_alphazero_search.py`: finite tree, masked/fallback priors, normalized probabilities, bounded simulations, terminal values, visit/Q reuse, retained and changed faction signs, temperature-zero choice. |
| 7-8 | Search/training-helper tests: Arena legality, scores, player swap and odd counts, win/loss/draw accounting; two-step Coach heuristic episode; skip/accept/reject/draw branches, queue/history bounds, checkpoint calls/naming, actual example pickle and missing-file prompts. |
| 9-10 | `ml/test_alphazero_training_helpers.py`: hand-computed losses, tiny-network predict/checkpoints, real AtlatlNNet forward and forced eval-dropout characterization, AverageMeter and dotdict/pickle. Concrete collaborators exercise the used interface protocol. Interface-only Game/NeuralNet stubs and empty initializers are excluded. |
| 11 | `ml/test_alphazero_orchestration.py`: short real game, both-act TypeError, neither-progress detected after ten iterations at an observation boundary, main load/no-load recording orchestration with inert logging. Explicit imports resolve historical README path assumptions without symlinks. |
| 12-14 | Script tests use real NumPy/SciPy, import-time output, mean/SEM, paired comparison, malformed data, generated archives, missing file/key, fixed-port binding double and real ephemeral HTTP body/MIME/cache headers. |
| 15-16 | `scripts/test_examples.py`: all four unchanged SB3 examples use recording model/environment/evaluation/callback boundaries, redirected chdir and finite episodes. Retrieved MyCNN classes use real tensors. All three PortableTorch demos intercept absolute source-output paths and large constructors; no demo persistence integration is claimed. gym_main's unconfigured real Gymnasium import failure is characterized. |

Known contracts K48-K51 use strict exact-signature defect probes. Other named
characterizations are observations rather than approved future requirements.
Coach's constant curPlayer, unchanged red feature score, wider-action conversion,
undefined training device, missing-checkpoint TypeError and forced dropout are
documented limitations. This suite does not claim GPU, real SB3 training, arbitrary
board dimensions, or rotational/reflection symmetry coverage.
