from pathlib import Path
import textwrap

OUT = Path(__file__).with_name("Parallel_Computing_Easy_Answers.pdf")

# Plain ASCII is deliberate: the PDF uses built-in Helvetica/Courier fonts,
# so it opens without any external font files.
sections = [
("How to read the answers", [
"This guide rewrites the sixteen questions in direct, exam-friendly language. The formulas give the usual asymptotic model. Let t_calc be the time for one multiply-accumulate, t_s the message startup time, and t_w the time per byte. Constants vary slightly with the machine and network; the important idea is stated beside each formula.",
"Notation: A, B, C are n x n matrices and C = AB. p is the processor count. q = sqrt(p) for a square processor grid. A processor array has fixed local neighbor links; a multiprocessor shares memory. A multicomputer has separate memories and sends messages."]),
("Q1. Sequential matrix multiplication", [
"For every output position (i,j), compute the dot product of row i of A and column j of B.",
"Algorithm:\nfor i = 0 to n-1\n  for j = 0 to n-1\n    C[i][j] = 0\n    for k = 0 to n-1\n      C[i][j] = C[i][j] + A[i][k] * B[k][j]",
"There are n^2 output entries. Each needs n multiply-add operations, so the running time is T1 = Theta(n^3). The storage for the three matrices is Theta(n^2)."]),
("Q2. Processor array versus multiprocessor", [
"A processor array is a regular collection of simple processing elements (PEs), usually laid out as a line or mesh. PEs run the same instruction at the same time on different data (SIMD) and normally communicate with nearby PEs.",
"A multiprocessor has a smaller number of full processors that share one main memory. Each processor can execute its own instruction stream (MIMD), so it is more flexible but must coordinate access to shared data.",
"The SIMD matrix multiplication algorithm uses a processor array. One PE is assigned to each output entry or block, and all PEs perform the same multiply-accumulate instruction together."]),
("Q3. Matrix multiplication on an n x n mesh", [
"Use n^2 PEs P(i,j), one for each C[i,j]. Put A[i,0] at the left edge of row i and B[0,j] at the top edge of column j. At every clock step, a values move one place right, b values move one place down, and each PE multiplies the two values currently meeting there and adds the result to its local C value.",
"Data flow (arrows show the direction of travel):\n  A row:  A[i,k] ---> ---> --->\n                         P(i,j): C[i,j] += A[i,k] * B[k,j]\n  B column:        |\n                   v B[k,j]",
"The kth pair needed at P(i,j) is delivered by the row and column pipelines. After the pipeline fills, every PE works each step. The last answer appears after about 2n - 1 steps, hence Tp = (2n - 1)t_calc = Theta(n), if movement and one multiply-accumulate fit in a step. This very low time uses n^2 PEs; it does not mean the total work is smaller."]),
("Q4. Shared-memory row-wise block-striped algorithm", [
"Divide A and C into p contiguous horizontal strips, each with about n/p rows. Processor r computes every C[i,j] in its assigned rows and reads the common matrix B from shared memory. No other processor writes those C rows, so locks are not needed for the arithmetic. A barrier is used when all strips are complete.",
"Ideal computation time: Tp = (n^3/p)t_calc. More realistically, Tp = (n^3/p)t_calc + T_memory + T_barrier, where the added terms cover shared-memory traffic and synchronization.",
"With sequential time T1 = n^3 t_calc, speedup is S = T1/Tp and efficiency is E = S/p = T1/(pTp). If memory contention is small, S is close to p and E is close to 1. When many processors repeatedly read B or compete for memory bandwidth, Tp rises and both measures fall."]),
("Q5. 1-D row-wise algorithm on a multicomputer", [
"Each processor owns n/p rows of A and computes the matching rows of C. Every processor needs all of B, so B is broadcast (or replicated during distribution). It then performs the same three nested loops only for its local rows.",
"Computation time: T_comp = (n^3/p)t_calc. On a tree network, broadcasting B costs approximately T_comm = log(p)[t_s + (8n^2)t_w] for 8-byte entries. A ring gives a different constant, but it still sends a full n x n B matrix through the network.",
"The main communication overhead is the replication of B. Initial scattering of A and collection of C may also be counted. As p grows, each processor computes fewer rows but still needs the full B, so communication eventually dominates. This is why the 1-D method scales poorly at large p."]),
("Q6. 4 x 4 mesh: skewing and first three steps", [
"Use indices 0,1,2,3. Initially skew A row i left by i places and B column j up by j places. Thus PE P(i,j) first holds A[i,(i+j) mod 4] and B[(i+j) mod 4,j]. Each step it adds their product to C[i,j], then shifts A left and B up by one place.",
"The number k used by every PE in the first three product steps is:\nstep 1:  0 1 2 3       step 2:  1 2 3 0       step 3:  2 3 0 1\n          1 2 3 0                2 3 0 1                3 0 1 2\n          2 3 0 1                3 0 1 2                0 1 2 3\n          3 0 1 2                0 1 2 3                1 2 3 0",
"For example, at step 1 P(2,1) adds A[2,3]B[3,1]; at steps 2 and 3 it adds A[2,0]B[0,1] and A[2,1]B[1,1]. Step 4 supplies the remaining k value. Therefore four multiply-accumulate steps are required after the initial skewing. The pre-skew can be performed by the same neighbor links."]),
("Q7. Cannon's algorithm on a q x q multicomputer grid", [
"Let q = sqrt(p), and give each processor one (n/q) x (n/q) block of A, B, and C. First skew A block (i,j) left by i positions and B block (i,j) up by j positions. Then repeat q times: multiply the local A and B blocks into C; shift A left one processor and B up one processor, with wraparound.",
"Grid idea:\n A blocks move left:  [P00] <--- [P01] <--- [P02]\n B blocks move up:       ^         ^         ^\n                         [P10]    [P11]    [P12]",
"Each processor does n^3/p arithmetic. With a block size n^2/p entries, a common message model is:\nTp = (n^3/p)t_calc + 2(q-1)[t_s + 8(n^2/p)t_w].\nThe factor 2 counts the A and B shifts; hardware that overlaps them can reduce the constant.",
"Compared with 1-D striping, Cannon's algorithm sends small blocks only to neighbors instead of broadcasting all of B. It is therefore more scalable. Its latency-related isoefficiency is roughly Theta(p^(3/2)), while 1-D replication becomes communication-bound much sooner."]),
("Q8. Numerical comparison: p = 64, n = 1024", [
"Assumption: t_calc = 10 ns is one multiply-accumulate, entries are 8 bytes, and initial placement/final collection are excluded. Sequential time is T1 = n^3 t_calc = 10.7374 s. Here q = sqrt(64) = 8.",
"(a) 1-D row-wise. Computation = (n^3/64)t_calc = 0.167772 s. One B broadcast has 6 tree stages. A stage costs 50 microseconds + (1024^2 x 8 x 20 ns) = 0.167822 s. Thus Tcomm = 6 x 0.167822 = 1.006933 s and Tp = 1.174705 s. Speedup S = 10.7374/1.174705 = 9.14. Efficiency E = 9.14/64 = 0.143 (14.3%).",
"(b) 2-D checkerboard/Cannon. A block is 128 x 128 entries. One block shift costs 50 microseconds + (128^2 x 8 x 20 ns) = 0.002671 s. There are 2(8-1) shifts, so Tcomm = 0.037400 s and Tp = 0.205172 s. S = 10.7374/0.205172 = 52.33. E = 52.33/64 = 0.818 (81.8%). If A and B shifts overlap, the 2-D result is still better.",
"Choose the 2-D method. It keeps communication local and moves much smaller blocks, giving far higher speedup and efficiency for these values."]),
("Q9. The two phases of Gaussian elimination", [
"Gaussian elimination solves Ax = b in two phases. First, forward elimination uses row operations to turn A into an upper triangular matrix U. It also updates b to a new right-hand side y. This phase performs about n^3/3 arithmetic operations, so it is Theta(n^3).",
"Second, back substitution finds x[n-1], then x[n-2], and so on using the triangular equations. It takes about n^2/2 operations, so it is Theta(n^2). The forward phase dominates the total sequential running time, which is Theta(n^3)."]),
("Q10. Jacobi iteration and convergence", [
"For Ax = b, Jacobi computes every new component from values in the previous iteration:\nx_i^(k+1) = ( b_i - sum over j != i of a_ij x_j^(k) ) / a_ii,   for i = 1,...,n.",
"All x_i^(k+1) values use the old vector x^(k), so they can be calculated in parallel. Do not replace one old value with a new value halfway through an iteration; that would be Gauss-Seidel, not Jacobi.",
"A useful sufficient condition for convergence is strict diagonal dominance in every row: |a_ii| > sum over j != i of |a_ij|. The exact condition is spectral radius rho(D^(-1)(L+U)) < 1. Stop when the change or residual is below a chosen tolerance."]),
("Q11. Parallel Gaussian elimination with cyclic rows and pivoting", [
"Assign row i to processor i mod p. This cyclic (striped) placement spreads the shrinking set of active rows across processors better than giving each processor one large block. At elimination step k, processors find the largest |a[i,k]| among their local active rows. A global reduction chooses the pivot row, which is swapped into position k, then the pivot row is broadcast.",
"Every processor updates its local rows i > k: multiplier = a[i,k]/a[k,k], then row_i = row_i - multiplier x pivot_row. The pivot-row broadcast supplies the n-k values needed by all processors. At the end, back substitution also needs broadcasts of newly known x values.",
"Arithmetic is Theta(n^3/p). A standard message estimate is Tp = Theta((n^3/p)t_calc + n t_s log p + n^2 t_w), plus row-swap and synchronization costs. The n log p term comes from reductions/broadcast startups; n^2 bandwidth comes from all pivot rows. Partial pivoting improves numerical safety but adds the max reduction and possible row movement."]),
("Q12. Parallel Jacobi on p processors", [
"Give each processor about n/p rows of A, b, and the corresponding entries of x_new. Every processor reads the old full vector x, computes its assigned equations, and writes its own part of x_new. Then all processors exchange their portions so that each has the full new vector for the next iteration.",
"Local arithmetic per iteration is Theta(n^2/p), hence T_comp = Theta((n^2/p)t_calc). If a tree-style all-gather is used, a simple conservative communication estimate is T_share = Theta(t_s log p + 8n t_w log p). A ring all-gather has different startup/bandwidth constants but sends the same total vector information.",
"Therefore T_iter = Theta((n^2/p)t_calc + T_share). Repeating until convergence gives total time = (number of iterations) x T_iter. The exchange of x_new, not the row computation, is the key communication cost."]),
("Q13. Enumeration sort on a CRCW PRAM", [
"Give a processor to every ordered pair (i,j), so n^2 processors compare A[i] with A[j] in parallel. The rank of A[i] is the number of values smaller than it. To make equal values stable, also count an equal A[j] when j < i:\nrank(i) = count{j : A[j] < A[i] or (A[j] = A[i] and j < i)}.\nThen write A[i] into output[rank(i)].",
"For 7, 3, 9, 1, 5, 4 the ranks are:\nvalue:  7  3  9  1  5  4\nrank:   4  1  5  0  3  2\noutput: [1, 3, 4, 5, 7, 9]",
"With a CRCW model that supports the required concurrent counting/reduction, this is O(1) parallel time using O(n^2) processors. On a PRAM that must reduce each set of comparisons with a binary tree, the rank accumulation is O(log n). Its processor cost is high, so it is mainly a theoretical parallel algorithm."]),
("Q14. Odd-even transposition sort", [
"Place one value in each processor of a line. In odd phases compare-exchange pairs (1,2), (3,4), ... . In even phases compare-exchange pairs (2,3), (4,5), ... . A compare-exchange leaves the smaller value on the left and the larger on the right.",
"Trace for [8,3,7,1,6,2,5,4]:\nstart [8,3,7,1,6,2,5,4]\nodd   [3,8,1,7,2,6,4,5]\neven  [3,1,8,2,7,4,6,5]\nodd   [1,3,2,8,4,7,5,6]\neven  [1,2,3,4,8,5,7,6]\nodd   [1,2,3,4,5,8,6,7]\neven  [1,2,3,4,5,6,8,7]\nodd   [1,2,3,4,5,6,7,8]\neven  [1,2,3,4,5,6,7,8]",
"In one phase a value can move at most one position. The smallest item may need to travel from the far right to the far left, a distance of n-1. Thus n phases are sufficient (and the worst case needs Theta(n) time) with n processors."]),
("Q15. Bitonic sort and bitonic merge", [
"A bitonic sequence first increases then decreases, or any cyclic shift of such a sequence. Example: [1,2,6,7,8,5,4,3] is bitonic. A bitonic merge compares elements distance n/2 apart, puts each smaller one in the low half and larger one in the high half, and recursively merges both halves.",
"Example merge for eight values:\n[1,2,6,7,8,5,4,3]\ndistance 4 -> [1,2,4,3 | 8,5,6,7]\ndistance 2, then 1 -> [1,2,3,4 | 5,6,7,8]",
"Bitonic sort makes a bitonic sequence by recursively sorting the first half upward and the second half downward, then applying an upward bitonic merge. For eight elements: sort two groups of four in opposite directions, concatenate them, then merge as above.",
"A merge has log2(n) compare stages. Bitonic sort has log2(n) merge levels, so depth is O(log^2 n). A comparator network uses n/2 comparators per stage; a hypercube implementation commonly uses n processors, one item per processor, for the same O(log^2 n) time."]),
("Q16. Quicksort-based parallel sorting", [
"In parallel quicksort, choose a pivot, split keys into less-than and greater-than-or-equal groups, send the two groups to two processor groups, and repeat independently. On a p-processor hypercube, p = 2^d. At hypercube stage r, paired processors exchange the part of their local lists that belongs in the other half. After d = log2(p) stages, each processor has the keys for one final range and sorts its local list.",
"Good pivots make each split close to half-and-half. Random pivots give good balance in expectation; sample medians or median-of-medians improve balance at extra cost. With balanced partitions, a useful expected estimate is:\nTp = O((n/p) log n + (n/p) log p + t_s log p).\nThe first term includes local sorting and useful work; the other terms represent repeated redistribution and message latency. Details vary by network and pivot method.",
"Speedup degrades with bad pivots because one processor group receives most keys and becomes the bottleneck. It also degrades when n/p is too small, because startup and routing dominate, when many duplicate keys are not split evenly, or when pivot selection itself is expensive. Parallel quicksort works well only when partitioning keeps both data and work reasonably balanced."]),
]

W, H = 595, 842
LEFT, RIGHT, TOP, BOTTOM = 48, 48, 55, 48
LEADING = 13
BODY_SIZE = 9.4


def esc(text):
    return text.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')


def make_page(lines, page_no):
    cmds = ["q", "0.12 0.20 0.36 rg", "BT /F2 16 Tf 48 808 Td (Parallel Computing: Easy Answers) Tj ET",
            "0.45 0.48 0.55 RG 48 798 m 547 798 l S", "0 g"]
    y = 778
    for kind, text in lines:
        if kind == 'heading':
            size, font, gap = 11.5, 'F2', 5
        elif kind == 'code':
            size, font, gap = 8.2, 'F3', 0
        elif kind == 'formula':
            size, font, gap = 9.0, 'F3', 0
        else:
            size, font, gap = BODY_SIZE, 'F1', 0
        cmds.append(f"BT /{font} {size} Tf {LEFT} {y:.1f} Td ({esc(text)}) Tj ET")
        y -= LEADING + gap
    cmds += ["0.45 0.48 0.55 RG 48 35 m 547 35 l S", "0 g",
             f"BT /F1 8 Tf 48 22 Td (Simplified study notes | Page {page_no}) Tj ET", "Q"]
    return '\n'.join(cmds)


def prepare_lines():
    raw = []
    for idx, (title, paragraphs) in enumerate(sections):
        raw.append(('heading', title))
        for p in paragraphs:
            if '\n' in p:
                for sub in p.split('\n'):
                    if sub.startswith(('for ', '  for', '    ', '      ', 'step ', 'value:', 'rank:', 'output:', 'start ', 'odd  ', 'even ', 'distance ', ' A ', ' B ', 'Grid')) or '[' in sub and '->' not in sub:
                        raw.append(('code', sub))
                    elif '=' in sub or 'Theta' in sub or 'O(' in sub or 'rho' in sub:
                        raw.append(('formula', sub))
                    else:
                        for line in textwrap.wrap(sub, width=92, break_long_words=False, break_on_hyphens=False) or ['']:
                            raw.append(('body', line))
            else:
                for line in textwrap.wrap(p, width=96, break_long_words=False, break_on_hyphens=False):
                    raw.append(('body', line))
            raw.append(('body', ''))
    return raw


def paginate(lines):
    pages, current, used = [], [], 0
    max_lines = 53
    for kind, text in lines:
        cost = 1
        if used + cost > max_lines:
            pages.append(current)
            current, used = [], 0
        current.append((kind, text))
        used += cost
    if current:
        pages.append(current)
    return pages


def build_pdf(page_streams):
    objects = []
    # 1 catalog, 2 pages, 3 Helvetica, 4 Helvetica-Bold, 5 Courier
    objects.extend([
        "<< /Type /Catalog /Pages 2 0 R >>",
        None,
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>",
    ])
    page_ids = []
    for stream in page_streams:
        content_id = len(objects) + 2
        page_id = len(objects) + 1
        page_ids.append(page_id)
        data = stream.encode('latin-1')
        objects.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {W} {H}] /Resources << /Font << /F1 3 0 R /F2 4 0 R /F3 5 0 R >> >> /Contents {content_id} 0 R >>")
        objects.append(f"<< /Length {len(data)} >>\nstream\n{stream}\nendstream")
    objects[1] = "<< /Type /Pages /Kids [" + ' '.join(f"{x} 0 R" for x in page_ids) + f"] /Count {len(page_ids)} >>"
    result = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(result))
        result.extend(f"{i} 0 obj\n{obj}\nendobj\n".encode('latin-1'))
    xref = len(result)
    result.extend(f"xref\n0 {len(objects)+1}\n0000000000 65535 f \n".encode())
    for off in offsets[1:]:
        result.extend(f"{off:010d} 00000 n \n".encode())
    result.extend(f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    OUT.write_bytes(result)
    return len(page_streams), len(result)


if __name__ == '__main__':
    pages = paginate(prepare_lines())
    count, size = build_pdf([make_page(lines, i + 1) for i, lines in enumerate(pages)])
    print(f"Wrote {OUT.name}: {count} pages, {size} bytes")
