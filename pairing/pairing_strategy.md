# Outline of the pairing strategy:

1. Determine if there are an odd number of players
    If there are find the lowest scoring player without a bye and give them a bye
1. Take all remaining players and construct a graph with a single edge between each pair of players

    Weights for the graph are as follows:
    - Side cost determination -> for a possible side assignment determine if they've already played it. If they have not the see if the pairing puts them further from balance on net (so |p1.balance| + |p2.balance| >= |p1.balance + 1| + |p2.balance - 1| if checking if player 1 is corping). So to elaborate out some cases further:
        - If both players are at 0 this is ignored
        - If p1 had a +1 side balance and p2 had a +1 side balance the pairing is "fine" because the net imbalance will be the same
        - If p1 had a +1 side balance and p2 had a 0 side balance the pairing is "bad" because that would increase the imbalance to 3
        - If p1 had a -1 side balance and p2 had a 0 side balance the pairing is "fine" because the total imbalance would remain the same
        - If p1 had a -1 side balance and p2 had a +1 side balance the pairing is "fine" because the total imbalance would decrease
    - Then the cost of the final side balance is calculated (8^(sum of abs balance)) or set to 1000 if it's a "bad permuation
    - Then the score cost of the pairing is calculated as the triangular product (because it scales nicely with the power of 8)
        - (corp_score + runner score) * (corp_score + runner score -1) / 6
    - The edge value is set to 1000 - (the sum of the side balance cost and score differential cost) 
        - So closer score and opposite sides will increase the edge value
1. Use [max_weight_matching](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.matching.max_weight_matching.html) algorithm to find a pairing that maximizes the total value
1. Assign pairings based on that (currently recompute because I don't store them anywhere, but it's only 2*number of matches)
1. Create the bye player table