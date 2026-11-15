"""Create an annotated PDF without changing any original assignment page.

The first 28 pages are copied byte-for-byte from the supplied assignment.  The
new pages are appended as a plain-language guide that explains the original
answers and decodes their formulas.  No image, diagram, or formula on an
original page is removed, redrawn, or changed.
"""
from pathlib import Path
import re
import textwrap

SOURCE = Path(__file__).with_name("Parallel_Computing_Assignment-1.pdf")
OUTPUT = Path(__file__).with_name("Parallel_Computing_Easy_Answers.pdf")

# These are explanations of the same algorithms and formulas, not replacement
# questions. Formula lines are deliberately written in the simpler notation
# students see in the original assignment.
GUIDE = [
("Guide purpose", [
"The first part of this PDF is the original 28-page assignment. It is kept exactly as supplied, so every original figure, table, and formula stays in the same form. This second part explains the same answers in easier language.",
"For formula reading: n means matrix size, so an n x n matrix has n rows and n columns. p means number of processors. T1 means time on one processor, Tp means time on p processors, S means speedup, and E means efficiency. Theta(...) describes how running time grows when n becomes large."]),
("Q1. Sequential matrix multiplication", [
"To multiply A by B, we make one value of C at a time. For C[i,j], take row i from A and column j from B. Multiply matching positions and add the products. For example, C[0,0] = A[0,0]B[0,0] + A[0,1]B[1,0] + ... + A[0,n-1]B[n-1,0]. The same idea is repeated for every row and every column.",
"The three loops have a simple meaning: i chooses a row of A, j chooses a column of B, and k walks through the n pairs that must be multiplied. There are n choices for i, n for j, and n for k. Therefore the work is n x n x n = n^3 operations.",
"Formula decoded: T1 = Theta(n^3). This does not mean the answer takes exactly n^3 seconds. It means that if n doubles, the amount of arithmetic becomes about 2^3 = 8 times larger. The n^3 term is the important growth term."]),
("Q2. Processor array and multiprocessor", [
"A processor array is a regular group of small processors arranged in a pattern such as a line, square, or mesh. They usually all receive the same instruction together but work on different data. This is called SIMD: Single Instruction, Multiple Data. A processor array is very suitable when every part of a problem follows the same repeated step.",
"A multiprocessor has several general-purpose processors connected to the same shared memory. Each processor can run a different instruction stream. This is called MIMD: Multiple Instruction, Multiple Data. It is flexible, but processors can slow each other down when they all need the same memory.",
"For the SIMD matrix multiplication described in the assignment, use a processor array. Many processing elements perform one multiply-and-add at the same time on different matrix entries."]),
("Q3. n x n processor mesh", [
"Imagine n^2 processors placed in n rows and n columns. Processor P(i,j) is responsible for one answer, C[i,j]. Values from row i of A travel across that processor row. Values from column j of B travel down that processor column. Whenever the correct A[i,k] and B[k,j] meet at P(i,j), the processor multiplies them and adds the result to its private accumulator.",
"At the start, the first values of A are placed at the left side of each row, and the first values of B are placed at the top of each column. At each clock step, A values move right by one processor and B values move down by one processor. This is a pipeline: after the first few steps, many useful multiplications happen at the same time.",
"Formula decoded: Tp = (2n - 1)t_calc = Theta(n). t_calc is the time for one multiply-accumulate step. The first result needs data to travel to it, and the last result needs data to travel out, which explains the 2n - 1 pipeline steps. The time is small only because the machine uses n^2 processors."]),
("Q4. Shared-memory block-striped multiplication", [
"Split A into p wide horizontal strips. If p divides n, each strip has n/p rows. Give one strip of A, and the same rows of C, to each processor. All processors can read the full B matrix from shared memory. A processor calculates all columns of C for only its own rows, so no two processors try to write the same output entry.",
"Each processor performs about (n/p) x n x n = n^3/p multiply-add operations. When every processor finishes, the full C matrix is ready. A barrier is often used so that no later step starts too early.",
"Formula decoded: Tp = (n^3/p)t_calc + overhead. The first part is ideal arithmetic time. Overhead includes waiting at the barrier and delays caused by many processors reading B from memory. Speedup S = T1/Tp tells how many times faster the parallel run is. Efficiency E = S/p tells what fraction of the p processors is effectively used. E = 1 is ideal; lower E means time was lost to overhead."]),
("Q5. Row-wise multiplication on a multicomputer", [
"A multicomputer is different from shared memory: every processor has its own private memory. Divide A by rows as before. Processor r stores roughly n/p rows of A and produces the matching rows of C. However, it cannot simply read B from a common memory. It needs a local copy of B before it can calculate its rows.",
"The usual solution is to broadcast B: send the complete B matrix to all processors. Then local multiplication costs n^3/p operations, just as in the shared-memory row split. The difference is that sending B takes time on the network.",
"Formula decoded: Tcomp = (n^3/p)t_calc. A tree broadcast is often written Tcomm = log(p)[t_s + m t_w], where m is the message size in bytes. Here m is about 8n^2 for 8-byte entries. t_s is startup time, paid once per message stage. t_w is time per byte. The important overhead is that every processor needs the whole B matrix, even though each computes only a few rows of C."]),
("Q6. 4 x 4 mesh skewing example", [
"Skewing means shifting the A and B data before the main multiplication begins. For a 4 x 4 processor mesh, shift A row i left by i positions and shift B column j up by j positions. The shifts wrap around at the edges. The purpose is to make each processor receive a pair with the same inner index k at the same time.",
"After skewing, P(i,j) first multiplies A[i,(i+j) mod 4] by B[(i+j) mod 4,j]. The word mod means remainder after division. For example, (3+2) mod 4 = 1, so index 5 wraps to index 1. At the next step both inputs shift again and the processor receives the next k value.",
"Formula decoded: C[i,j] = sum from k=0 to 3 of A[i,k]B[k,j]. Each processor must add four products, one for each k. Therefore there are four multiply-accumulate stages after initial skewing. The original figure shows the first three stages; the fourth stage supplies the last missing product."]),
("Q7. Cannon's algorithm", [
"Cannon's algorithm is the block version of the skewing idea. Arrange p processors as a q x q grid, where q = sqrt(p). Divide A, B, and C into q x q blocks. Each processor owns one block from each matrix. Before calculating, processor block A(i,j) is shifted left by i places and B(i,j) is shifted up by j places.",
"Then repeat q times: multiply the two local blocks and add the result to the local C block; shift A one place left; shift B one place up. Only neighboring processors exchange blocks. The blocks wrap around at the edge of the grid. After q rounds, each C block has received every block product it needs.",
"Formula decoded: Tp = (n^3/p)t_calc + 2(q-1)[t_s + 8(n^2/p)t_w]. The first term is local arithmetic. A local block has n^2/p entries, and 8 converts entries to bytes for double-precision data. The 2(q-1) term represents A and B block shifts. Unlike the 1-D method, Cannon sends small neighbor blocks instead of broadcasting the full B matrix, so it usually scales better."]),
("Q8. Meaning of the numerical estimates", [
"For n = 1024 and p = 64, one processor would perform n^3 multiply-accumulates. With t_calc = 10 ns, T1 = 10.7374 seconds. The 1-D method gives each processor 1024/64 = 16 rows, so its arithmetic time is only 0.167772 seconds. But it still broadcasts the complete 1024 x 1024 B matrix, which is 8,388,608 bytes.",
"A tree broadcast takes log2(64) = 6 stages. One stage takes t_s + m t_w = 50 microseconds + 8,388,608 x 20 ns = 0.167822 seconds. Communication therefore costs about 1.006933 seconds, much more than the local arithmetic. Total 1-D time is about 1.174705 seconds, speedup about 9.14, and efficiency about 14.3 percent.",
"For 2-D, q = 8 and each local block is 128 x 128. A message contains only 131,072 bytes. The communication is about 0.037400 seconds and total time about 0.205172 seconds. So speedup is about 52.33 and efficiency about 81.8 percent. The 2-D checkerboard/Cannon method is preferred because its messages are much smaller and stay between neighbors."]),
("Q9. Gaussian elimination phases", [
"Gaussian elimination solves Ax = b in two parts. First is forward elimination. It uses row operations to make the entries below the diagonal zero. At the end, A becomes an upper triangular matrix U. The right-hand side b changes at the same time.",
"Second is back substitution. Start with the last equation, which has only one unknown. Find the last x value, substitute it into the equation above, and continue upward until every x value is known.",
"Formula decoded: forward elimination is Theta(n^3), because it updates a large remaining part of the matrix in each of n stages. Back substitution is Theta(n^2), because each of n unknowns uses at most n already-known values. Since n^3 grows faster than n^2, forward elimination determines the overall sequential complexity."]),
("Q10. Jacobi iteration", [
"Jacobi is an iterative method. It begins with a guess for x. To calculate a new x_i, use all the old values from the previous iteration. Do this for every row, then replace the old vector only after all new values have been computed.",
"Formula decoded: x_i^(k+1) = [b_i - sum(j not equal to i) a_ij x_j^(k)] / a_ii. The superscript k means the old iteration number. First multiply each off-diagonal coefficient a_ij by the old x_j, add those products, subtract from b_i, and divide by the diagonal coefficient a_ii. This gives the next value x_i.",
"A simple condition that guarantees convergence is strict diagonal dominance: |a_ii| > sum(j not equal to i)|a_ij| for every row. In plain language, each diagonal number must be larger in magnitude than all other numbers in its row added together. Then the repeated guesses move toward the solution."]),
("Q11. Parallel Gaussian elimination", [
"In cyclic row partitioning, row i is stored on processor i mod p. This spreads the active rows among processors even near the end of elimination, when few rows remain. At step k, every processor checks the possible pivot values in column k among its local rows. A reduction selects the row with the largest absolute value. This is partial pivoting.",
"The owner of the selected row swaps it into pivot position k. The pivot row is broadcast to all processors. Each processor then updates the rows it owns below the pivot: it computes a multiplier and subtracts multiplier times the pivot row. These row updates happen in parallel.",
"Formula decoded: arithmetic is about n^3/p. The communication is commonly written n t_s log(p) + n^2 t_w. There are about n elimination stages. Each stage needs a reduction and broadcast, which create startup costs. Pivot rows together contain about n^2 data values, which create bandwidth cost. Pivoting is worth this cost because it avoids dividing by a very small, inaccurate pivot."]),
("Q12. Parallel Jacobi", [
"Give each processor about n/p rows of A and b. It calculates the same entries of x_new. Every processor needs the old complete x vector, because a row can use any x_j. After local work, processors share their portions of x_new so everyone has the full vector for the next iteration.",
"The local work is about n/p rows times n multiplications per row, so it is n^2/p operations per iteration. The processors must also communicate n values in total to reconstruct x_new everywhere.",
"Formula decoded: T_iter = Theta((n^2/p)t_calc + T_share). T_share is the time for the vector exchange. With a tree communication pattern it is often described by startup time proportional to log(p), plus a per-byte cost for the n vector values. If the number of iterations is I, total time is I x T_iter. The number I depends on the matrix and chosen error tolerance."]),
("Q13. Enumeration sort", [
"Enumeration sort finds the final position, called the rank, of every value. With n^2 PRAM processors, processor P(i,j) compares value i with value j. All comparisons happen at the same time. For a value, count how many values are smaller than it. That count is its rank starting from zero.",
"For 7, 3, 9, 1, 5, 4: rank(7)=4 because 1,3,4,5 are smaller; rank(3)=1; rank(9)=5; rank(1)=0; rank(5)=3; rank(4)=2. Put each number into its rank position. The result is [1,3,4,5,7,9].",
"For repeated values, use the original index as a tie-breaker: count A[j] as before when A[j] < A[i], or when A[j] = A[i] and j < i. Formula decoded: n^2 processors means one comparison processor for every pair. In the ideal CRCW model, ranking and writing take O(1) parallel time. Practical machines need more careful reductions, so they may take O(log n) to add comparison results."]),
("Q14. Odd-even transposition sort", [
"Put one number in each processor along a line. In an odd phase, compare neighbors (1,2), (3,4), and so on. In an even phase, compare neighbors (2,3), (4,5), and so on. Each pair swaps if it is in the wrong order. A small value can move one position left in a phase, and a large value can move one position right.",
"For the given list, the original trace shows the values becoming more ordered after every odd and even phase. The 1 moves left one neighbor at a time until it reaches the first processor. The 8 moves right one neighbor at a time until it reaches the last processor.",
"Formula decoded: Tp = Theta(n) with n processors. A value may have to cross n-1 links, and it can cross only one link per phase. Therefore n phases are enough. This algorithm is easy to implement on a line, but its running time grows linearly, so it is slower than sorting networks with logarithmic-depth stages."]),
("Q15. Bitonic sort", [
"A bitonic sequence goes up and then down, or is a circular shift of such a sequence. For example, 1,2,6,7,8,5,4,3 is bitonic. Bitonic merge turns this into sorted order by comparing entries that are halfway apart. Put the smaller result in the first half and the larger result in the second half. Then do the same independently inside each half.",
"Bitonic sort creates this special shape on purpose. Sort the first half upward and the second half downward. Their combination is bitonic. Finally apply a bitonic merge in the required direction. The same rule is used recursively for 2, 4, 8, and then larger numbers of elements.",
"Formula decoded: one merge has log2(n) compare stages because the comparison distance halves each time: n/2, n/4, ..., 1. Bitonic sort has log2(n) recursive levels, and each level needs a merge. Therefore time is O(log^2 n). A network uses n/2 comparators in one stage, while a hypercube version normally uses n processors, one item per processor."]),
("Q16. Parallel quicksort on a hypercube", [
"Parallel quicksort repeats the usual quicksort idea in groups of processors. Choose a pivot. Each processor separates its local values into less-than-pivot and greater-than-or-equal-to-pivot parts. Processor pairs exchange the part that belongs to the other group. Then the two processor groups continue independently with their own pivots.",
"A hypercube with p = 2^d processors has d = log2(p) splitting stages. At each stage, one dimension of the hypercube connects matching processor pairs. After all stages, each processor holds values from one final range and can sort its small local list.",
"Formula decoded: a balanced expected time is O((n/p)log n + (n/p)log p + t_s log p). n/p is the average local list size. The first term is useful sorting work; the second is data moved across log p split stages; the last is message startup. Good pivots keep both groups near equal size. A bad pivot sends most values to one group, leaving others idle and destroying speedup. Speedup also falls when p is too large for n, when messages dominate, or when many equal keys are handled unevenly."]),
]

W, H = 595.92, 842.88
LEFT, TOP = 48, 778
LEADING = 13.5
MAX_LINES = 47


def esc(s):
    return s.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')


def line_kind(text):
    if text.startswith('Formula decoded:'):
        return 'formula'
    return 'body'


def prepare_lines():
    lines = []
    for title, paragraphs in GUIDE:
        lines.append(('heading', title))
        for paragraph in paragraphs:
            for line in textwrap.wrap(paragraph, width=91, break_long_words=False, break_on_hyphens=False):
                lines.append((line_kind(line), line))
            lines.append(('spacer', ''))
    return lines


def paginate(lines):
    pages, page = [], []
    for item in lines:
        if len(page) >= MAX_LINES:
            pages.append(page)
            page = []
        page.append(item)
    if page:
        pages.append(page)
    return pages


def page_stream(lines, number, total):
    commands = [
        'q',
        '0.12 0.20 0.36 rg',
        'BT /F2 15 Tf 48 808 Td (Plain-Language Guide to the Original Assignment) Tj ET',
        '0.45 0.48 0.55 RG 48 798 m 547 798 l S',
        '0 g',
    ]
    y = TOP
    for kind, text in lines:
        if kind == 'heading':
            font, size, extra = 'F2', 11.2, 3.5
        elif kind == 'formula':
            font, size, extra = 'F3', 8.8, 1.5
        elif kind == 'spacer':
            y -= 4
            continue
        else:
            font, size, extra = 'F1', 9.3, 0
        commands.append(f'BT /{font} {size} Tf {LEFT} {y:.2f} Td ({esc(text)}) Tj ET')
        y -= LEADING + extra
    commands.extend([
        '0.45 0.48 0.55 RG 48 35 m 547 35 l S',
        '0 g',
        f'BT /F1 8 Tf 48 22 Td (Part 2 of this PDF: explanation pages {number} of {total}) Tj ET',
        'Q',
    ])
    return '\n'.join(commands)


def latest_startxref(data):
    matches = list(re.finditer(rb'startxref\s*(\d+)\s*%%EOF', data))
    if not matches:
        raise ValueError('Cannot find source PDF startxref')
    return int(matches[-1].group(1))


def new_pdf_objects(streams):
    # Original PDF ends at object 2151. Object 2152 is a new page-tree root.
    root_id, regular_id, bold_id, mono_id = 2152, 2153, 2154, 2155
    objects = {
        86: '<< /Type /Pages /Count 28 /Kids [82 0 R 83 0 R 84 0 R 85 0 R] /Parent 2152 0 R >>',
        2014: '<< /Type /Catalog /Pages 2152 0 R /ViewerPreferences << /DisplayDocTitle true >> /Lang (en) >>',
        regular_id: '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
        bold_id: '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>',
        mono_id: '<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>',
    }
    page_ids = []
    next_id = 2156
    for stream in streams:
        page_id, content_id = next_id, next_id + 1
        next_id += 2
        page_ids.append(page_id)
        raw = stream.encode('latin-1')
        objects[page_id] = (
            '<< /Type /Page /Parent 2152 0 R /MediaBox [0 0 595.92 842.88] '
            '/Resources << /Font << /F1 2153 0 R /F2 2154 0 R /F3 2155 0 R >> >> '
            f'/Contents {content_id} 0 R >>'
        )
        objects[content_id] = f'<< /Length {len(raw)} >>\nstream\n{stream}\nendstream'
    objects[root_id] = (
        '<< /Type /Pages /Kids [86 0 R ' + ' '.join(f'{pid} 0 R' for pid in page_ids) +
        f'] /Count {28 + len(page_ids)} >>'
    )
    return objects


def append_incremental_update(source, objects):
    result = bytearray(source)
    if not result.endswith(b'\n'):
        result.extend(b'\n')
    positions = {}
    for object_id in sorted(objects):
        positions[object_id] = len(result)
        result.extend(f'{object_id} 0 obj\n{objects[object_id]}\nendobj\n'.encode('latin-1'))
    xref_position = len(result)
    ids = sorted(positions)
    groups = []
    group = [ids[0]]
    for object_id in ids[1:]:
        if object_id == group[-1] + 1:
            group.append(object_id)
        else:
            groups.append(group)
            group = [object_id]
    groups.append(group)
    result.extend(b'xref\n')
    for group in groups:
        result.extend(f'{group[0]} {len(group)}\n'.encode())
        for object_id in group:
            result.extend(f'{positions[object_id]:010d} 00000 n \n'.encode())
    old_xref = latest_startxref(source)
    size = max(ids) + 1
    result.extend(
        f'trailer\n<< /Size {size} /Root 2014 0 R /Info 1 0 R /Prev {old_xref} >>\n'
        f'startxref\n{xref_position}\n%%EOF\n'.encode()
    )
    return result


if __name__ == '__main__':
    source = SOURCE.read_bytes()
    pages = paginate(prepare_lines())
    streams = [page_stream(page, i + 1, len(pages)) for i, page in enumerate(pages)]
    OUTPUT.write_bytes(append_incremental_update(source, new_pdf_objects(streams)))
    print(f'Wrote {OUTPUT.name}: original 28 pages preserved + {len(pages)} guide pages')
