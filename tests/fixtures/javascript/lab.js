// Лабораторная: простые числа
function isPrime(n) {
  if (n < 2) return false;
  for (let d = 2; d * d <= n; d++) {
    if (n % d === 0) return false;
  }
  return true;
}

class Counter {
  constructor() { this.count = 0; }
  add(step = 1) {
    this.count += step;
    return this.count;
  }
}

function main() {
  const limit = Number(prompt("Предел?"));
  const primes = [];
  for (let i = 2; i <= limit; i++) {
    if (isPrime(i)) primes.push(i);
  }
  console.log("Простые:", primes.join(", "));
  console.log(`Всего ${primes.length}`);
  for (const p of primes) {
    if (p > 50) break;
  }
  switch (primes.length % 2) {
    case 0:
      console.log("чётное");
      break;
    default:
      console.log("нечётное");
  }
  try {
    JSON.parse("{");
  } catch (e) {
    console.error("ошибка:", e.message);
  } finally {
    console.log("готово");
  }
}

const c = new Counter();
let x = 0;
while (x < 3) {
  x = c.add();
}
main();
