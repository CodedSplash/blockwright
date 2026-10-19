// A sample for the Rust description:
//     python -m blockwright --lang-dir docs/example-rust --lang rust docs/example-rust

fn gcd(mut a: u64, mut b: u64) -> u64 {
    while b != 0 {
        let t = a % b;
        a = b;
        b = t;
    }
    a
}

fn main() {
    let n: u64 = 12;
    for i in 1..=n {
        if i % 2 == 0 {
            continue;
        }
        println!("НОД({}, {}) = {}", i, n, gcd(i, n));
    }
    let mut k = 0;
    loop {
        k += 1;
        if k > 10 {
            break;
        }
    }
    match n % 3 {
        0 => println!("кратно трём"),
        1 | 2 => {
            println!("остаток {}", n % 3);
        }
        _ => unreachable!("остаток больше двух"),
    }
}
