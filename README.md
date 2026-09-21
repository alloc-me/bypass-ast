Формат AST:
  Операторы:
    "skip"
    {"read": "x"}
    {"write": expr}
    {"assn": {"dst": "x", "src": expr}}
    {"seq": {"left": stmt, "right": stmt}}
    {"if": {"cond": expr, "then": stmt, "else": stmt}}
    {"while": {"cond": expr, "body": stmt}}
    {"do": {"body": stmt, "cond": expr}}
  Выражения:
    {"const": 5}
    {"var": "x"}
    {"binop": "+", "left": expr, "right": expr}

Пример программы:
```
{
  read(n);
  k = 3

  write(n + k);
  write(n - k);
  write(n * k);
  write(n / k);
  write(n % k);

  write(n == k);
  write(n != k);
  write(n < k);
  write(n <= k);
  write(n > k);
  write(n >= k);

  write(n > 0 && k > 0);
  write(n < 0 !! k < 0);

  x = 10;
  x += 5;
  x -= 3;
  x *= 2;
  x /= 4;
  x %= 4;
  write(x);
  
  s = 0;
  i = 1;
  while (i <= n) {
    s += i;
    i += 1
  }
  write(s);

  do {
    write(k);
    k -= 1
  } while (k > 0);

  f = 1;
  for (i = 1; i <= n; i += 1) f *= i;
  write(f);

  if (n % 2 == 0) write(2)
  elif (n % 3 == 0) write(3)
  else write(0);

  if (k == 0) write(777);

  if (n > 0) skip else write(999)
}
```
