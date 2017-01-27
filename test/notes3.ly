\version "2.18.2"

\paper {
  indent = 0
  paper-height = 3\cm
  paper-width = 7\cm
}

\header {
  tagline = ##f
}

\pointAndClickOff

\relative {
  c' d e f |
  g1_\fermata
  \bar "|."
}
